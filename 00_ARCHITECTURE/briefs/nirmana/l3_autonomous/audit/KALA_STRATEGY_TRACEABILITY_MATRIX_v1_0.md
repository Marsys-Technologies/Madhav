---
artifact: KALA_STRATEGY_TRACEABILITY_MATRIX
version: "1.0"
status: DRAFT — cycle 3 of the KĀLA READINESS AUDIT
produced_by: L3 Kāla readiness audit (autonomous, Claude Code)
produced_on: 2026-09-22
scope: T1 — for each of the 22 active `ka_*` identities plus protected `ka_gochara_sweep`, the
  full traceability row per AUDIT_CHARTER.md / PROMPT_0_ENVIRONMENT_AND_ARCHITECTURE_AUDIT.md §2 T1.
method: >
  Produced by 3 parallel read-only subagents, one per stream cluster defined in
  MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md §4 ("The three streams"): Frontier (9 assets), Spine
  (11 assets — the source document's own header says "10" but lists 11 names; both sub-agents and
  this integration retain all 11 per the audit's "flag, don't drop" rule), Kshetra+Century
  (2 assets, with ka_sangam/ka_kala_darshana additionally cross-listed here since they were
  ambiguously scoped in the original task briefs and the charter instructs "better in 2 reports
  than none" — their authoritative home is Spine). Each subagent's headline claims were
  independently spot-verified by the conductor via direct DB query or grep before integration
  (see AUDIT_STATE.md cycle 3 for the verification log). `ka_gochara_sweep` (protected, retired,
  outside the 22-denominator) is claimed by none of the three streams per the elevation plan's own
  text — this is itself an orphan-obligation finding, recorded below.
---

# KĀLA STRATEGY TRACEABILITY MATRIX — T1 (the central deliverable)

For each active `ka_*` identity: contribution-register disposition + DP obligations → L3 strategy
row (A-nn) + required transformation → L3-Q questions → product P-nn questions → proving
journey(s) → U-nn consumer interface(s) → receiving operator that exists today → F13/F14 ladder
position under the CURRENT campaign definition `t3-2026-09-11-8b884eac`.

**Cross-cutting fact, confirmed independently in all three clusters and by F2's direct query:**
under `t3`, **zero of the 22 active `ka_*` identities have any campaign event of any type.** The
F13/F14 ladder columns below report code/data state honestly, but no asset in this document has
climbed past `PLAN_REVIEWED` on the campaign's own evidentiary ladder — see
`KALA_ACCEPTANCE_REGIME_MAPPING_v1_0.md` (T3) for why, and `F2.md` for the per-asset ancestor
lineage that is the only pre-t3 evidence any of them carry.

---

# PART 1 — Stream A: Frontier (9 assets)

**Cluster definition:** `MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md` §4, line 134 — explicit, no
judgment call: `ka_graha_sancara`, `ka_dasha_kala`, `ka_muhurta_seva`, `ka_gochara_resonance`,
`ka_kota_chakra`, `ka_moorti_nirnaya`, `ka_sudarshana_varsha`, `ka_tithi_pravesha`,
`ka_vedha_gochara`. All T0. "Upstream of both other streams — must run first and fastest."
Independently corroborated: these 9 are (with 3 Spine assets) exactly the 12-asset set that
reached an ancestor `asset_frozen` event, per F2's DB query — all frozen under
`t0-2026-09-01-0e5b06fb`, none under `t3`.

## `ka_graha_sancara`

- **Disposition + DP:** "Position/motion service." P/I/Q: arbitrary instant/frame provenance;
  self-test is bounded service proof. DP07. (REGISTER:134)
- **L3-A01:** Ephemeris/Swiss service probe; zero materialized rows. Required: preserve numerical
  service/state safety; prove exact conventions, time, arbitrary-chart input, provenance,
  failures — a canonical probe is not full service qualification. Wave W2. (STRAT:271)
- **L3-Q (inferred, not source-stated):** Q01, Q03, Q09.
- **P-nn (inferred):** P09–10/P22, P09, P13/P19.
- **Proving journeys:** foundational/indirect in all three — supplies the geometry substrate, not
  named as a row-serving asset in any journey text.
- **U-nn:** none. Gap — see Orphan Obligations.
- **Receiving operator today:** **DIVERGENT.** `call_ephemeris_at_t` calls the sidecar's own
  `/api/compute/ephemeris_at_t` route with its own separate `import swisseph`, explicitly *not*
  `services/ka_graha_sancara/engine.py` (F5, high confidence). The live path is a parallel
  implementation, not this writer's own code.
- **F13/F14 under t3:** present (service exists, no dedicated table) → not consumed by its own
  name → qualified/consumed/served/value-evaluated beyond that: COULD NOT VERIFY. Ancestor
  `asset_frozen` = yes (t0); events under t3 = 0.

## `ka_dasha_kala`

- **Disposition + DP:** "Clock retrieval, ancestry and system traversal." P/E/I/Q: precise ISO
  intervals, actual overlap/applicability/failed-system coverage; label approximate subdivisions.
  DP07/08. (REGISTER:135)
- **L3-A02:** L1 `chart_dashas` service probe across seven systems; zero rows. Required: preserve
  L1 clock authority; expose actual hierarchy, applicability, intervals, failed/silent systems,
  qualified overlap; no layer-local clock restatement. Wave W2. (STRAT:272)
- **L3-Q:** Q01, Q05, Q06 (direct content match).
- **P-nn:** P09–10/P22 (Q01), P15/P19/P21 (Q05), P10 (Q06).
- **Proving journeys:** directly named in §12.1 ("which qualified clocks engage those same
  participants") and implied in §12.3 (original clock window for a frozen claim).
- **U-nn:** closest is U02, but `kala_dasha_sandhi_get` reads L1 `chart_dashas` directly, not any
  `ka_dasha_kala`-owned table — consistent with, and corroborating, the receiving-operator finding.
- **Receiving operator today:** **NOT-FOUND — real gap.** `call_dasha_eligibility` runs a raw SQL
  query directly against L1 `chart_dashas`; no `KaDashaKalaService` import found anywhere; no
  `target_table`/`INSERT INTO` hits in `services/ka_dasha_kala/writer.py`. F5's own conclusion:
  unclear whether this writer's own output is consumed anywhere at all.
- **F13/F14 under t3:** present (writer exists) → consumption status is the open question itself,
  arguably blocked (no writer output has a confirmed consumer) → effect-traceable onward: not
  reached. Ancestor `asset_frozen` = yes (t0); events under t3 = 0.

## `ka_muhurta_seva`

- **Disposition + DP:** "Calendar/action-time computation and search service." P/I/Q: calendar
  correctness, personal suitability, outcome are distinct; real undertaking constraints/scope.
  DP07/09. (REGISTER:156)
- **L3-A03:** Panchanga/election service probe; zero rows. Required: test actual time/location and
  undertaking constraints; distinguish general calendar from personal feasibility/outcome
  expectation. Wave W2 (real accepted-input use W7). (STRAT:273)
- **L3-Q:** Q10 (near-verbatim match); also named in elevation-plan Q7 ("nearest vs strongest" —
  `tulana, muhurta_seva, kalasutra`), an open native-discussion item.
- **P-nn:** P11/P21–22.
- **Proving journeys:** **not named** in §12.1–12.3 despite being the direct answer to P11 — flagged
  as a real gap.
- **U-nn:** none found.
- **Receiving operator today:** LIVE, medium confidence — `call_muhurta_score` and
  `muhurta_finder.ts` reuse `score_muhurat()` per an in-file comment (primitive source itself not
  independently re-confirmed).
- **F13/F14 under t3:** present, consumed (medium confidence). Ancestor `asset_frozen` = yes (t0);
  events under t3 = 0.

## `ka_gochara_resonance`

- **Disposition + DP:** "Event-target assembly and provenance." P/I/Q/C: reconcile structural
  compilation with Yojaka/Kshetra, preserving unique roles rather than rival promise definitions.
  DP06/08. (REGISTER:136)
- **L3-A05:** `gochara_resonance_map` — chart × class × target type/reference, weights/rule
  citations. Required: preserve target discovery; dedup must not retain only first root; target
  contact is not automatic mechanism activation. Wave W2. (STRAT:275)
- **L3-Q:** Q07, Q03.
- **P-nn:** P01/P03–10/P17 (Q07), P09 (Q03).
- **Proving journeys:** candidate evidence for §12.2 NBRY (eligible activation routes/closest
  contact) — inferred, not named.
- **U-nn:** none found.
- **Receiving operator today:** **LIVE, high confidence, exact table match** — writer inserts
  `gochara_resonance_map`; consumer `register_gochara_windows.ts:1007` reads the same table
  exactly. Cleanest match of all 9 Frontier assets.
- **F13/F14 under t3:** present, consumed (high confidence). Ancestor `asset_frozen` = yes (t0);
  events under t3 = 0.

## `ka_kota_chakra`

- **Disposition + DP:** "Ring/run primitives and method-specific posture." P/I/Q: actual source
  geometry/scope; not an independent adverse vote by default. DP02/08. (REGISTER:138)
- **L3-A07:** `kala_kota_chakra` — chart × ayanamsha × graha × interval start, rings/severity/
  roots. Required: preserve ring testimony, exact version/applicability; pinned authority, not
  mutable latest-version. **"Current v3 implementation does not consume it: qualify and prove any
  proposed integration."** Wave W2. (STRAT:277)
- **L3-Q:** Q03 (inferred); named as "not an independent adverse vote by default" in T5's
  integrator analysis.
- **U-nn:** **not covered** — DOMAIN_F's U03 names similar witness assets but not this one.
- **Receiving operator today:** **LIVE, high confidence table match — but in tension with STRAT.**
  Writer targets `kala_kota_chakra`; `query_kota_chakra.ts` + `kala_views/now.ts` read it directly.
  STRAT:277 says the v3 pipeline specifically does not consume it. Two different consumer claims,
  not reconciled by any prior packet.
- **F13/F14 under t3:** present (585 rows canonical chart), consumed at the `now.ts` surface while
  simultaneously not consumed by the century-materialize v3 pipeline — different F13 rungs
  depending on which consumer is asked about. Ancestor `asset_frozen` = yes (t0); events under
  t3 = 0.

## `ka_moorti_nirnaya`

- **Disposition + DP:** "Run detection and truncated-ingress safeguards." P/I/Q: source-adjudicate
  implemented 27-nakshatra convention before broader authority. DP02/08. (REGISTER:139)
- **L3-A06:** `kala_moorti_nirnaya` — chart × ayanamsha × graha × interval start, quality.
  Required: qualify rolling −60/+400-day, day-grade Lahiri coverage and reference-offset handling;
  preserve method-native result, no silent century-complete reuse. **"Actual v3 input."** Wave W2.
  (STRAT:276)
- **L3-Q:** Q05 (inferred). Stronger current integration than kota_chakra (explicit "actual v3
  input").
- **U-nn:** not covered.
- **Receiving operator today:** **LIVE, high confidence, STRAT-confirmed actual v3 input** — writer
  targets `kala_moorti_nirnaya`; `query_moorti_nirnaya.ts` + `now.ts` read it directly.
- **F13/F14 under t3:** present (71 rows canonical chart), consumed (strongest F13 position of the
  9 Frontier assets, corroborated by the strategy doc itself). Ancestor `asset_frozen` = yes (t0);
  events under t3 = 0.

## `ka_sudarshana_varsha`

- **Disposition + DP:** "Annual three-reference wheel." P/I/Q: preserve actual annual scope; not
  static `bo_sudarshana` duplication or proof of full sub-daśā. DP07/08. (REGISTER:141)
- **L3-A10:** `kala_sudarshana_varsha` — chart × ayanamsha × year, three reference-frame results.
  Required: preserve frame-specific annual testimony; shared natal roots are not three independent
  witnesses. **"Current v3 does not read it; integration requires a qualified operator, not a
  dependency label."** Wave W2. (STRAT:280)
- **L3-Q:** Q05; directly implicated in elevation-plan Q3 ("what counts as an independent witness —
  Sangam treats shared natal roots as independent; Sudarshana's three frames share roots too").
- **U-nn:** not covered.
- **Receiving operator today:** LIVE, medium-high confidence, but **STRAT explicitly says the live
  v3 pipeline does not read it** — same tension pattern as kota_chakra.
- **F13/F14 under t3:** present (120 rows canonical chart), consumed at query-file level while STRAT
  disputes whether the production v3 pipeline consumes it. Ancestor `asset_frozen` = yes (t0);
  events under t3 = 0.

## `ka_tithi_pravesha`

- **Disposition + DP:** "Return bracketing, annual-chart and numerical search kernels." P/Q/E:
  named method/equation needs source adjudication; current Moon-longitude return is not accepted
  merely from name. DP02/07. (REGISTER:142)
- **L3-A09:** `kala_tithi_pravesha` — chart × ayanamsha × year, return graha/lagna and convergence.
  Required: qualify implemented Moon-return method against the admitted method before promotion;
  add explicit use decision. **"Current v3 does not read it."** Wave W2. (STRAT:279)
- **L3-Q:** Q06, Q05; directly implicated by elevation-plan Q2 ("three assets consumed by nothing
  today — `ka_kota_chakra`, `ka_tithi_pravesha`, `ka_sudarshana_varsha`. Wire them into a qualified
  operator, or retire with evidenced disposition?").
- **U-nn:** not covered.
- **Receiving operator today:** **The sharpest source-tension in the Frontier cluster.** F5 finds a
  LIVE, high-confidence, exact-table-match consumer (`query_tithi_pravesha.ts` + `now.ts` reading
  `kala_tithi_pravesha` directly) — yet the elevation plan's own Q2 groups this asset among three
  "consumed by nothing today." Flagged, not resolved; already logged as elevation-plan Q2.
- **F13/F14 under t3:** present (120 rows canonical chart); "consumed" is **contested** between F5
  (yes) and the elevation plan (no). Ancestor `asset_frozen` = yes (t0); events under t3 = 0.

## `ka_vedha_gochara`

- **Disposition + DP:** "Typed obstruction and disclosed approximations." P/I/Q: target-specific
  role/dependence; avoid duplicate attenuation. DP02/08. (REGISTER:140)
- **L3-A08:** `kala_vedha_gochara` — chart × ayanamsha × obstruction kind × graha × interval,
  school/root data. Required: preserve distinct schools, target/role, signed inhibition/sources;
  same evidence must not attenuate twice through TRIGGER and Vighnakara. **"Actual Sangam/v3
  input."** Wave W2. (STRAT:278)
- **L3-Q:** Q04 (direct match), Q03.
- **P-nn:** P03–04.
- **Proving journeys:** candidate evidence for §12.2 ("opposing conditions with scope and
  uncertainty") and plausibly §12.1's "unresolved retention constraint."
- **U-nn:** **U03**, directly named — the only Frontier asset with a confirmed, named U-id.
- **Receiving operator today:** **LIVE, high confidence, exact table match** — writer targets
  `kala_vedha_gochara`; three consumers (`query_vedha_gochara.ts`,
  `L0_brahmagyan/query_transit_vedha.ts`, `now.ts`) all read it directly.
- **F13/F14 under t3:** present (177 rows canonical chart), consumed (high confidence, U03=Y) — the
  only Frontier asset with both a named U-id and a clean, uncontradicted receiving-operator match.
  Ancestor `asset_frozen` = yes (t0); events under t3 = 0.

### Orphan obligations — Frontier

1. **No U-id covers 6 of the 9 Frontier assets** (`ka_graha_sancara`, `ka_muhurta_seva`,
   `ka_gochara_resonance`, `ka_kota_chakra`, `ka_moorti_nirnaya`, `ka_sudarshana_varsha`,
   `ka_tithi_pravesha` — 7 actually, on recount, excluding only `ka_vedha_gochara` [U03] and
   `ka_dasha_kala` [U02, bypassed in practice]). Either the U-list under-covers witness-tier
   assets, or these assets genuinely lack a stated product obligation — not resolved.
2. **`ka_muhurta_seva` has no proving-journey citation** despite being the direct answer to P11 and
   the subject of its own L3-Q10 row. Possibly sampling (Product §12 only illustrates 3 of ~24
   P-ids), not asserted as a defect.
3. **`ka_gochara_sweep`'s stream is undefined** — not named in Stream A/B/C at all. No cluster
   currently owns a T1 row for it under the strict Frontier/Spine/Kshetra+Century partition.

### Orphan work — Frontier

1. **`ka_kota_chakra` and `ka_moorti_nirnaya` have full, high-confidence, dedicated consumer
   surfaces with no U-id claiming them** — real served code with no named product obligation.
2. **`ka_sudarshana_varsha` and `ka_kota_chakra` each carry a live query-file consumer while STRAT
   says the production v3 pipeline does not read them** — possibly a shadow/legacy path rather than
   the intended integration; not resolved.
3. **`ka_tithi_pravesha`'s receiving operator is itself disputed** (F5: consumed, high confidence;
   elevation-plan Q2: consumed by nothing) — the highest-priority reconciliation item in this
   cluster; directly contradictory prior-cycle evidence, not merely an uncovered obligation.

---

# PART 2 — Stream B: Spine (11 assets)

**Cluster definition:** `MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md` §4, lines 143–144. **Source
off-by-one, flagged not resolved:** the section header says "Spine (10 assets)" but the roster
lists 11 names: `avadhi`, `yojaka`, `gochara`, `sangam`, `kalasutra`, `vighnakara`, `taranga`,
`kala_darshana`, `tulana`, `bhavishya_lekha`, `jivana_parva`. All 11 are covered below per the
audit's "include and flag, don't drop" rule. Three axes reported per asset since "code path
exists ≠ campaign-event exists": (a) code-present, (b) canonical-chart-data-present (F7), (c)
campaign-event-present under t3 (F2) — **all 11 Spine assets show 0 events under t3.**

## 1. `ka_avadhi`

- **Disposition + DP:** "Period dossiers with L1 references... enrich qualified
  participant/condition context and share with chapters." DP08/10. (REGISTER:153,
  `W/ka_avadhi.py:176`)
- **L3-A12:** `kala_avadhi` — chart × clock system × level × start, lords/dates/domain
  quality/citations. Required: preserve clock hierarchy; assess missing ayanamsha, fixed domains,
  ten-row limits, soft-empty behavior. Reads L0/L1/L2, not Yojaka; **Taranga currently does not
  read it.** Proposed W2. (STRAT:282)
- **L3-Q (inferred):** Q01, Q06.
- **P-nn:** P09–10/P22 (Q01), P10 (Q06).
- **Proving journeys:** Financial-promise §12.1 ("which qualified clocks engage those same
  participants") — inferred natural supplier of clock enumeration.
- **U-nn:** none of U01–U11 names it directly; actual live consumer is `kala_temporal.ts`'s
  `query_dasha_dossier` capability, outside the numbered U-list — orphan obligation.
- **Receiving operator today:** LIVE — `kala_temporal.ts` → `query_dasha_dossier` →
  `kala_avadhi`, documented as the fix that superseded the DARK `kala_timeline.ts`/`kala_timeline`
  pair (CR-40/T-1, 2026-07-16). `kala_timeline.ts` itself is confirmed **DARK on three axes**
  (never registered on the MCP server, not whitelisted on the primitives route, no writer targets
  `kala_timeline`) while still claiming the same "KA-3-1 kala.timeline" asset id — a
  documentation/identity collision, not a functional gap for avadhi.
- **F13/F14 under t3:** present, canonical-chart data 1,169 rows (single build 2026-08-12) →
  plausibly consumed (LIVE wiring) → served: COULD NOT VERIFY. Campaign events under t3 = 0 (2
  ancestor defs, neither reached `asset_frozen`).

## 2. `ka_yojaka`

- **Disposition + DP:** "Typed activation predicates and fired-yoga participant lookup... full
  mechanism compiler; preserve paired CDLM signals/roles and method key, not net domain average."
  DP05/06/08. (REGISTER:147, `W/ka_yojaka.py:479-510`)
- **L3-A11:** `kala_activation_predicates` — chart × ayanamsha × signal × predicate signature,
  eligibility/trigger/strength payloads. Required: compile complete accepted L2 mechanisms,
  participants, signed multidomain relations, cancellation, all linked roots; remove
  one-domain/five-link flattening. **79 unmatched MSR references must resolve** (independently
  re-confirmed: 79 of 50,678 rows, 0.156%, per F7 §4a). (STRAT:281)
- **L3-Q:** Q03 (direct match — mechanism compiler), Q01.
- **U-nn:** **U01**, names Yojaka explicitly: "Y — served via `kala_views/{ahead,priority,ritual,
  story}.ts` per F5."
- **Receiving operator today:** F5 rates both candidate consumers (`query_temporal_activation.ts`,
  the `kala_views/{ahead,priority,ritual,story}.ts` family) **low-medium confidence** — neither
  trace confirms the consumer actually reads `kala_activation_predicates` (yojaka's own table)
  rather than a neighboring table. A real, flagged gap, same class as the confirmed
  `ka_tulana`/`ka_dasha_kala` divergences, not yet promoted to CONFIRMED.
- **F13/F14 under t3:** present (50,678 rows, largest populated Spine table), qualified: COULD NOT
  VERIFY (the 79-row MSR gap is exactly a qualification-blocking defect), consumed: low-medium
  confidence only. Campaign events under t3 = 0 (2 ancestor defs; **did** reach `asset_frozen`
  under t2 — superseded, inadmissible under t3).

## 3. `ka_gochara`

- **Disposition + DP:** "Contact/search numerics and generation-bearing materialization...
  separate service/writer/coverage from interpretive conclusion." DP07/08. (REGISTER:139,
  `W/ka_gochara.py:180`)
- **L3-A13:** `kala_gochara_windows_v2`, generation 2.0 — chart/class/shape/window, signed
  terms/valence/suppression. "Preserve v2 computation and bounded ±3-year search. **Materialized
  v2 rows are not Sangam's current transit input.**" Proposed W3. (STRAT:283)
- **L3-Q:** Q01, Q08.
- **Receiving operator today:** **DIVERGENT — confirmed FIVE-WAY disagreement**, wider than the
  three-way originally reported: STRAT + WRITER CODE + migration 1018's digest spec all say the
  writer's table is `kala_gochara_windows_v2` gen `2.0`; SEED + the LIVE CONSUMER
  (`register_gochara_windows.ts:581`) both point at the un-suffixed `kala_gochara_windows` gen
  `3.0` instead (T5 Tension 1). Additionally: `ka_sangam`'s declared `depends_on: ka_gochara` edge
  resolves in code to a *different* asset sharing the name — a namesake `services/ka_gochara/
  service.py` retained as a backward-compat alias (T5 Tension 7) — so even the DAG edge feeding
  off this asset is hollow.
- **F13/F14 under t3:** present (writer's own table `kala_gochara_windows_v2` = 1,001 rows;
  the table the consumer actually cites, `kala_gochara_windows` = 17,211 rows, not confirmed to be
  this writer's current output) → **qualified: BLOCKED** by the five-way table-identity defect.
  Campaign events under t3 = 0 (1 ancestor def, t1, reached `asset_frozen` there — superseded).

## 4. `ka_sangam`

- **Disposition + DP:** "Targeted/exploratory convergence and contact search... consume full
  configuration/domains/conditions, not first domain or missing-dignity 0.5." DP06/08.
  (REGISTER:148, `W/ka_sangam.py:331-377`) — T5 confirms both named defects (first-domain,
  missing-dignity-0.5) are **still present in code, unannotated**.
- **L3-A15, Tier S ("the three hard ones"):** `kala_convergence` — chart/signal/mode/window,
  score/orb/rarity/constituents. **"The chokepoint — 7 of 21 depend on it."** Required: remove
  hidden coverage caps and default independent-witness claims. Proposed W3. (STRAT:285;
  elevation plan:64)
- **L3-Q:** Q07, Q04.
- **U-nn:** no direct U-id, but per T5 it is "the common ancestor of five of the eight
  integrators" — any U-item touching `ka_kala_darshana`, `ka_vighnakara` (U03),
  `ka_bhavishya_lekha`, `ka_jivana_parva`, or `ka_taranga` is transitively reading Sangam's output
  presented as if independently corroborating.
- **Receiving operator today:** `query_convergence_windows.ts`, `query_temporal_activation.ts`,
  `kala_views/ahead.ts` — medium confidence.
- **F13/F14 under t3 — the single most significant finding in this cluster:**
  - Code-present: yes, extensively wired (7 declared dependents, chokepoint role confirmed).
  - **Canonical-chart data: `kala_convergence` = 0 rows** for the canonical chart (globally
    non-empty, 20,497 rows across 2 other charts). Sangam's own table has never been populated for
    this chart despite being described as "THE VALUABLE CORE." **Independently corroborated:**
    `asset_throughput` shows the writer *did* run for this chart on 2026-08-13, recorded writing
    14,868 rows, `state='stale'`, no `last_error` — the data existed once and is gone, unexplained
    (see T2 for the full cross-journey finding). **Also corroborated by F3:** of 23 identities,
    `ka_sangam` is one of 12 that has never been dispatched through a run whose manifest survived,
    "despite 522 build_runs existing for the canonical chart."
  - **F13: present is the honest ceiling.** Qualified/consumed/served/effect-traceable/
    value-evaluated are all **unreachable, not merely unverified** — nothing exists in
    `kala_convergence` for this chart.
  - **F14: strategy agreed only.** Producer ready is **NO** for the canonical chart specifically —
    wiring without data is not readiness.

## 5. `ka_kalasutra`

- **Disposition + DP:** "Deterministic interval resolution and recurrence... shared interval
  kernel with exact peak/horizon/truncation semantics; best-score selection is not nearest
  search." DP07/08. (REGISTER:149)
- **L3-A16:** `kala_activation` — chart × signal × ayanamsha × period, period-ID arrays and
  resolved windows/peaks. Required: retain all qualified recurrences/multiple convergence
  contributions; remove default-eight truncation, implicit today, redundant payloads. Proposed W4.
  (STRAT:286)
- **L3-Q:** Q02 (direct match).
- **U-nn:** **U04**, names Kalasutra explicitly, rated **Y** (the gap is on the Tulana half, not
  Kalasutra's).
- **Receiving operator today:** `query_temporal_activation.ts`; `kala_views/ahead.ts`, `now.ts` —
  **high confidence**, reads its own declared table plus a documented L2 join.
- **F13/F14 under t3 — second major finding, same shape as `ka_sangam`:**
  - **Canonical-chart data: `kala_activation` = 0 rows** for the canonical chart (globally
    non-empty, 337,148 rows, 100% owned by other charts). Despite F5's high-confidence same-table
    verdict, nothing exists for this chart. **Independently corroborated:** `asset_throughput`
    shows the writer ran 2026-08-13, recorded writing 335,403 rows, `state='stale'`, no
    `last_error`.
  - Campaign events under t3 = 0; and per F2 this is one of only 3 assets with **zero campaign
    evidence in any generation, ever** (the other two: `ka_gochara_v`, `ka_vighnakara`).
  - **F13: present ceiling only** — high-confidence code wiring to an empty table is evidence of
    correct wiring, not consumption/service/value.
  - **F14: strategy agreed only.** Never analyzed under any campaign definition.

## 6. `ka_vighnakara`

- **Disposition + DP:** "Explicit counter-indicator interface and astronomical calls... qualify
  detector, target, interval; distinguish one underlying obstruction from repeated
  representation." DP08. (REGISTER:150)
- **L3-A17:** `kala_obstruction` — chart/signal/optional convergence, kind/severity/override/
  roots. Required: preserve opposition separately from activity; resolve top-500 coverage,
  null-convergence association, deterministic ties, targeted applicability; no
  absence-of-evaluation as clear passage. Proposed W4. (STRAT:287)
- **L3-Q:** Q04 (direct match).
- **U-nn:** **U03**, names Vighnakara explicitly, rated **Y**.
- **Receiving operator today:** `query_obstruction_periods.ts` — high confidence, direct
  `FROM kala_obstruction` read.
- **F13/F14 under t3:** **Canonical-chart data: `kala_obstruction` = 0 rows** for the canonical
  chart (globally non-empty, 747 rows across 2 other charts) — third instance of the
  high-confidence-wiring-empty-table pattern. One of the 3 zero-campaign-evidence-ever assets
  alongside `ka_kalasutra`. T5's Tension 5 corroborates a structural independence defect even once
  data exists: `ka_kala_darshana`'s net score composes `ka_sangam` with `ka_vighnakara`, but
  `ka_vighnakara` itself reads `ka_sangam` — "so convergence × obstruction is not two independent
  readings; both legs descend from `ka_sangam`." **F14: strategy agreed only.** Producer ready is
  NO for the canonical chart.

## 7. `ka_taranga`

- **Disposition + DP:** "Coarse multiresolution trend projection... candidate projection of
  common qualified evidence; current grade/convergence averaging is not event probability."
  DP08/10. (REGISTER:152)
- **L3-A18:** `kala_taranga` — chart × month × scope kind/ID over 1950-2100. Required: preserve
  timeline signal; inspect raw Mahadasha context/ayanamsha and class-specific meaning; no invented
  Avadhi dependency. Proposed W4. (STRAT:288)
- **L3-Q:** Q06, Q02.
- **Receiving operator today:** `query_activation_waveform.ts` — medium confidence.
- **F13/F14 under t3:** present, **canonical-chart data 92,412 rows** (single build 2026-08-13) —
  one of only two Spine assets (with `ka_jivana_parva`) both wired and genuinely populated for the
  canonical chart. **Qualified is blocked** by T5's Tension 6: `ka_taranga` averages
  `kala_convergence` (from `ka_sangam`, L2 Bodha-enriched) with `bodha_pratijna` (same L2 Bodha
  substrate) — "the average reads as corroboration between two views of one source," exactly the
  DP08/10 defect the register already names. Campaign events under t3 = 0 (1 ancestor def, t2, did
  not reach `asset_frozen`).

## 8. `ka_kala_darshana`

- **Disposition + DP:** "Convergence/obstruction presentation join... qualify independent
  net-score authority; global top-750 and NULL→0.5 are not complete personalized search."
  DP08/10/12. (REGISTER:155) — T5 confirms a **real split**: the NULL→0.5 half is now annotated/
  warned-and-documented (never-firing per code comment), but the **top-750 global cut is
  unchanged and unqualified** with a live effect on every served row.
- **L3-A19:** `kala_darshana` — chart/convergence/signal/window, effective score and obstruction
  summary. Required: preserve the zero-handling repair; resolve top-750 truncation and
  missing-convergence 0.5 default; **"current computation reads convergence/obstruction, not
  `kala_activation` as the registry claims."** Proposed W5. (STRAT:289)
- **L3-Q:** Q01.
- **U-nn:** none named directly, but is the genuinely-LIVE half of `kala_temporal.ts`'s disputed
  "KA-3-1 kala.timeline" designation (via `query_temporal_view`), the counterpart to `ka_avadhi`'s
  half.
- **Receiving operator today:** `query_temporal_view.ts` — medium confidence, confirmed LIVE (not
  dark).
- **F13/F14 under t3:** **Canonical-chart data: `kala_darshana` = 0 rows** for the canonical chart
  (globally non-empty, 750 rows, all owned by chart `1c826d5a-…`) — fourth instance of the
  wired-but-empty pattern, and a direct downstream consequence of `ka_sangam`'s own empty state
  for this chart. Campaign events under t3 = 0 (1 ancestor def, t2, did not reach `asset_frozen`).

## 9. `ka_tulana`

- **Disposition + DP:** "Comparison service and factor breakdown... compare named
  outcomes/criteria, nearest/strongest/robust separately; self-test not consumer-value proof."
  DP08/17. (REGISTER:157)
- **L3-A04:** Pure `WindowInput` comparison service; synthetic probe, zero rows. Required: preserve
  useful ranking kernel; add matched mechanism/context, nearest vs. stronger/robust candidates,
  trade-offs, ties, incomparable states. Proposed W2 pure / W7 data-bound. (STRAT:274)
- **L3-Q:** Q02 (near-literal restatement).
- **U-nn:** **U04**, rated Y with a known gap: "per F5, `ka_tulana`'s consumer wrapper reads
  `kala_activation` (owned by `ka_kalasutra`), not any table traceable to `ka_tulana`'s own writer
  — the 'Tulana' half of this U-item has an open §N.8-flagged gap even though the tool itself is
  callable."
- **Receiving operator today:** **NOT-FOUND — confirmed by F5.** The consumer's SQL selects from
  `kala_activation` (a table `ka_kalasutra` owns); `grep target_table|INSERT INTO` on
  `ka_tulana/writer.py` found zero hits. Independently corroborated: no `kala_tulana` table exists
  anywhere in F7's 37-table census — consistent with the strategy doc's own "synthetic probe, zero
  rows" description.
- **F13/F14 under t3:** **present is ambiguous by design vs. defect, not merely unverified** — if
  `ka_tulana` is a pure stateless comparison service by design (per STRAT), "present" should be
  graded on service callability; if the consumer's `kala_activation` read is instead an
  undisclosed substitution (F5's unresolved alternative), "present" for tulana's own output is
  currently false, full stop. Campaign events under t3 = 0 (1 ancestor def, t2, reached
  `asset_frozen` there — superseded).

## 10. `ka_bhavishya_lekha`

- **Disposition + DP:** "Forward packaging and historical outcome references... shared qualified
  selection/claim boundary; top-100/five-year filter is not exhaustive future coverage; historical
  purpose isolated." DP08/12/15. (REGISTER:156)
- **L3-A21:** `kala_bhavishya` — chart × rank, tier/domain/window/falsifier/source plus retained
  outcomes. Required: preserve projection usefulness/observations; replace unstable rank identity;
  fix empty-input deletion path; **"rebuildable projections cannot own or rewrite issued
  history."** Proposed W6 after preservation gate. (STRAT:291)
- **L3-Q:** Q08, Q11.
- **Proving journeys:** **Historical-challenge journey (§12.3) — direct, not inferred.** "You
  predicted a promotion. It did not happen" requires retrieving "the original completed reading
  and frozen claim" — precisely this asset's stated job.
- **U-nn:** **U06** (Qualified stages→PACT/promise spine, via `ahead.ts`); **U09** (Historical
  comparison→prospective firewall) is conceptually this asset's exact job, though rated "Y (tool
  exists), firewall logic COULD NOT VERIFY."
- **Receiving operator today:** `query_projections.ts`; `kala_views/ahead.ts` — medium confidence.
- **F13/F14 under t3:** **Canonical-chart data: `kala_bhavishya` = 0 rows** for the canonical chart
  (globally non-empty, 100 rows, all owned by chart `1c826d5a-…`) — the most consequential of the
  five wired-but-empty findings, given this is the asset specifically responsible for D7
  history-safety: with zero rows there is currently no issued-claim history for this chart to
  protect or violate. T5's Tension 6 adds a qualification defect even once populated: three of
  four declared inputs trace to one producer (`ka_sangam`, directly and via `ka_kala_darshana`/
  `ka_vighnakara`) — a "triple-count risk" — plus the confirmed-present `LIMIT 100`/five-year
  truncation. Campaign events under t3 = 0.

## 11. `ka_jivana_parva`

- **Disposition + DP:** "Chapter hierarchy, birth clipping and references... current fine-period
  scope is running AD; enrich mechanisms rather than generic keywords; disclose coverage."
  DP08/10. (REGISTER:154)
- **L3-A20:** `kala_jivana_parva` — chart × level/index, year bounds/lord/theme/class. Required:
  preserve chapter hierarchy but retain exact interval/clock/context/mechanism links; replace
  unordered predicate `LIMIT 1` selection with a qualified relation. Proposed W6. (STRAT:290)
- **L3-Q:** Q06 (near-literal match).
- **Receiving operator today:** `query_life_arc.ts`; `kala_views/story.ts` — medium-high
  confidence, confirmed LIVE registration (`register_p1_synthesis.ts:726-764` →
  `kala_life_arc_get`).
- **F13/F14 under t3:** present, **canonical-chart data 100 rows** (single build 2026-08-13) — the
  second (with `ka_taranga`) genuinely wired-and-populated Spine asset. **Qualified is blocked** by
  T5's Tension 6: declared inputs include `ka_kala_darshana` (itself a `ka_sangam` composite) and
  `ka_sangam` directly — "chapter-level narrative agreement across these is agreement with
  `ka_sangam`, restated." Campaign events under t3 = 0 (1 ancestor def, t2, did not reach
  `asset_frozen`).

### Orphan obligations — Spine

1. `ka_avadhi` and `ka_kala_darshana` both genuinely serve the "kala.timeline"/"KA-3-1" asset label
   via `kala_temporal.ts`, but no U-nn item names either of them — a genuinely-live consumer
   capability with no owning U-id.
2. The `ka_yojaka` consumer-table binding has no confirmed owner (F5: low-medium confidence, table
   not verified) — if unconfirmed, `ka_yojaka` joins `ka_tulana`/`ka_dasha_kala` as a third asset
   whose own output may reach no confirmed consumer.
3. No campaign-event vocabulary exists for `CONSUMER_INTEGRATED` or `VALUE_EVALUATED` for any of
   these 11 assets (see T3/`KALA_ACCEPTANCE_REGIME_MAPPING_v1_0.md`) — cluster-spanning, not
   asset-specific.

### Orphan work — Spine

1. `ka_taranga`'s and `ka_jivana_parva`'s writers hold genuine canonical-chart data with live,
   registered consumers — yet neither shows any campaign event under t3, nor an ancestor
   `asset_frozen`. Real, working, served-eligible output invisible to `Accepted N/22`.
2. **"Wired orphan capacity"** — `ka_sangam`, `ka_kalasutra`, `ka_vighnakara`, `ka_kala_darshana`,
   `ka_bhavishya_lekha` all carry live or near-live consumer wiring aimed at tables holding zero
   rows for the canonical chart. Distinct failure mode from both orphan obligation and ordinary
   orphan work: the receiving operator would work the moment the writer runs for this chart, but
   nothing has triggered that run. Given `ka_sangam`'s chokepoint role, this is likely the
   single highest-leverage fix available in the Spine cluster.
3. `ka_gochara`'s writer output (`kala_gochara_windows_v2`, 1,001 rows) and the separately
   populated `kala_gochara_windows` (17,211 rows) both exist with live consumer code pointed at
   them, but only one can be the actual current writer's output per the five-way disagreement —
   whichever the consumer is not correctly reading is, by definition, orphan work.

---

# PART 3 — Stream C: Kshetra + Century (2 assets, primary) + `ka_sangam`/`ka_kala_darshana` (cross-listed)

**Cluster definition, corrected against source:** the original task brief's working description
("`ka_kshetra` + century + `ka_sangam` + `ka_kala_darshana`") does **not** match
`MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md` §4: Stream C is actually only **2 assets**: `ka_kshetra`,
`ka_gochara_v3_century_materialize` ("Two assets, more code than the other twenty combined...
near-independent; carries most of the performance programme"). `ka_sangam` (T2 tier) and
`ka_kala_darshana` (T4 tier) structurally belong to Stream B (Spine) — see Part 2 above for their
authoritative rows. Per the audit's "flag, don't drop" rule, abbreviated cross-reference rows for
both are retained below.

## `ka_kshetra` (Stream C, primary)

- **Disposition + DP:** "Typed stages, integration/search, provenance and uncertainty/selection
  machinery." P/E/I/Q: retain engineering; preserve signed edges, complete lineage,
  occurrence/condition, qualified clock jurisdiction before expanding model authority. DP06/07/08.
  (REGISTER:151)
- **L3-A22:** chart/class continuous field plus structural routes, kinematics, clocks, primitives,
  nulls, windows, provenance, salience, insights, snapshots. Required: treat as a staged data
  system, not one opaque writer; preserve continuous-field capital; recover full signed structural
  semantics, immutable inputs, exact null interpretation, useful projections, event-free purpose.
  Apply P0/P1/P2/P6 before expensive rebuilds. Internal W2–W7 DAG (STRAT §6.2): 9 data families,
  stage order S0 kinematics→S1 primitives; S2 structure/routes→S3 clocks/boundaries→S1;
  S0+S2+S3+S1→S4 field→S5 null/windows/provenance→S6 salience→S6.5 insights→S8 timeline→complete
  snapshot. (STRAT:292,295-324)
- **U-nn:** **L3-U01**, named explicitly: "Bind real producer fields, generations, signed routes,
  complete domains/roots... hydration must use exact accepted snapshots." Rated Y testable, served
  via `kala_views/{ahead,priority,ritual,story}.ts`.
- **Receiving operator today:** low-medium confidence (F5: "asset_id co-occurrence only, target
  table not independently verified").
- **F13: present, PARTIAL.** `kala_field` holds **8,570,075 rows** for the canonical chart, but
  `kala_field_snapshots` — the S8 "complete snapshot" terminus of Kshetra's own internal DAG — is
  **0 rows for the canonical chart** (1 row total, globally, belonging to a different chart). The
  elevation plan states this outright: "Its field snapshot has never been built for the canonical
  chart." **effect traceable: NO, actively contradicted** — "a served surface hard-codes 'field
  empty' (PARK-5)," corroborated by the dual-campaign execution plan: "`ka_kshetra` ~8.6M field
  rows with a served surface hard-coding 'field empty' (PARK-5)... partially populated with
  referential rot, not a clean slate." **served/value-evaluated: NO.**
- **F14:** PLAN_REVIEWED yes; PRODUCER_READY partial (14,113 LOC + 4,465 own tests exist, but
  rebuild is gated on P0/P1/P2/P6 first, and Q4 is an open native decision: "Is `ka_kshetra`'s
  continuous-field model the right abstraction to preserve?"). DATA_ACCEPTED/LAYER_DATA_ACCEPTED/
  CONSUMER_INTEGRATED: NO (PARK-5 directly contradicts). Campaign events: 1 ancestor def (t2),
  never reached `asset_frozen`; 0 events under t3.

## `ka_gochara_v3_century_materialize` ("the century materialiser", Stream C, primary)

- **Disposition + DP:** "Numerical refinement, resumability and wide-horizon coverage." P/Q/H:
  existing hold remains; **"eager century-wide work is not itself required user value."** No
  rematerialization. DP07/16. (REGISTER:140)
- **L3-A14:** Century staging and production windows: chart × class × era × resolution ×
  window/milestone, hierarchical parent IDs. Required: retain protected hold until
  authority/method decisions; redesign common preparation, target event searches, batched
  hierarchy writes; ensure complete overlay coverage, content-bound resume, coherent publication.
  **"Moorti/Vedha are actual inputs; Kota/Tithi/Sudarshana integration is not implemented."**
  Wave W3, after its specific hold is resolved. (STRAT:284)
- **Named unresolved decision:** T5's Tension 2 — REG:140's "no rematerialization" and STRAT:230-
  234's "deferral alone cannot earn full asset elevation" are in direct, unnamed-escape-branch
  tension for this exact asset. Elevation plan's **Q1**: "Full century materialisation, or a
  qualified compact substrate with explicit refinement semantics? The hold cannot close by
  deferral, and the answer changes ~11k LOC of work." T5's Tension 8 additionally finds the SEED's
  declared 6-edge `depends_on` set (including `ka_kota_chakra`, `ka_tithi_pravesha`) contradicts
  STRAT:284's own "Kota/Tithi/Sudarshana integration is not implemented" in the *same document* —
  two of six declared inputs are aspirational.
- **U-nn:** **none of L3-U01–U11 names this asset** — an orphan obligation in itself.
- **Receiving operator today:** `register_gochara_windows.ts` — F5 high confidence ("comment block
  explicitly names it authoritative writer"), but this claim sits inside the unresolved five-way
  table-identity dispute documented under `ka_gochara` above (Part 2, item 3).
- **F13: present, PARTIAL.** `kala_gochara_windows_v2` holds 1,001 rows for the canonical chart
  (`g3_utkarsha`→914, `2.0`→87); the `g3_utkarsha`-tagged rows are this asset's own era-slice
  output. Real prior-generation data exists under an active hold the register says should not be
  extended. **qualified: NO** (hold unresolved, Q1 open). **consumed: PARTIAL**, same table-identity
  caveat as `ka_gochara`.
- **F14:** PLAN_REVIEWED yes. PRODUCER_READY partial — 2,480 writer LOC + 8,441 `gochara_v3` LOC
  exist, but the writer's own declared input set overstates what it integrates; a readiness check
  run today "would report readiness it does not have." DATA_ACCEPTED: NO (explicitly held).
  LAYER_DATA_ACCEPTED: NO (STRAT's own definition: "a held or unqualified required active
  capability prevents full-layer acceptance" — this asset is exactly that holdout).
  **Entity-identity concern (COULD NOT VERIFY, flagged not asserted):** F2's per-asset table lists
  an entity `ka_gochara_v` (not the full asset id) with 0 ancestor defs, 0 events, ever — one of
  the "3 assets with zero campaign evidence in any generation." Not independently confirmed whether
  `ka_gochara_v` is a truncated/aliased entity_id for this asset or a genuinely distinct string —
  flagged for the conductor to resolve with a direct query.

## `ka_sangam` — cross-reference (authoritative row: Part 2, item 4, Spine)

Tier T2, "the chokepoint — 7 of 21 depend on it." **`kala_convergence` = 0 rows for the canonical
chart** despite being campaign's stated core asset; `asset_throughput` shows the writer ran once
(2026-08-13, 14,868 rows written, now `state='stale'`, data gone). See Part 2 for full detail.

## `ka_kala_darshana` — cross-reference (authoritative row: Part 2, item 8, Spine)

Tier T4. **`kala_darshana` = 0 rows for the canonical chart**, a direct downstream consequence of
`ka_sangam`'s own empty state for this chart. See Part 2 for full detail.

### Orphan obligations — Kshetra+Century

1. No U-nn interface packet names the century materialiser at all — REG:140/STRAT L3-A14 both
   impose real obligations with no receiving-operator interface packet assigned to carry them.
2. `ka_kshetra`'s U01 obligation exists in name but has no verified satisfying receiving operator
   — the only candidate is low-medium confidence and is directly contradicted by PARK-5.
3. `ka_sangam`'s frozen-manifest protection has never been exercised despite being the campaign's
   own named chokepoint (12 of 23 identities never captured by a surviving `plan_manifest`
   snapshot, "including `ka_sangam`, THE VALUABLE CORE") — whether properly this cluster's finding
   or Spine's is exactly the ambiguity this report was asked to flag rather than resolve.

### Orphan work — Kshetra+Century

1. `ka_kshetra`'s ~8.6M rows of built field data (plus `kala_field_provenance` 959,032,
   `kala_field_boundaries` 261,998, `kala_field_primitives` 165,082, five more populated
   `kala_field_*` tables) serve no currently-verified consumer — 14,113 LOC + 4,465 tests with the
   one referencing surface hard-coding an empty result (PARK-5).
2. `ka_kshetra`'s Stage 8 six-view grain is now-orphaned relative to current documented design
   direction: the value-architecture doc and product definition both state the six-view split "is
   not a target constraint" and should be projections, not a schema-enforced natural key — but
   `stage8_spec.py`'s `VIEWS` tuple and `kala_timeline_spec`'s natural key still hard-freeze
   exactly six views as a DB-enforced grain.
3. The century materialiser's declared 6-input dependency set includes 2 aspirational edges
   (`ka_kota_chakra`, `ka_tithi_pravesha`) contradicted by STRAT's own text in the same document —
   the inverse defect of orphan work (declared-but-absent), directly undermining any readiness
   signal drawn from the SEED for this asset.

---

# Cross-cluster synthesis

**The single dominant pattern across all 23 rows:** a cluster of Spine/Kshetra assets —
`ka_sangam`, `ka_kalasutra`, `ka_vighnakara`, `ka_kala_darshana`, `ka_bhavishya_lekha` — all show
**live or near-live consumer wiring pointed at tables holding zero rows for the canonical chart**,
while `asset_throughput` independently shows two of them (`ka_sangam`, `ka_kalasutra`) *did* write
substantial row counts for this chart on 2026-08-13 before going `stale` with no recorded error.
This is the same substrate gap T2 (`KALA_PROVING_JOURNEYS_BASELINE_v1_0.md`) finds is the first
failing boundary for all three proving journeys — this document arrives at it independently, from
the asset-obligation side rather than the journey-walkthrough side, and the two converge exactly.

**Second pattern:** table-identity disagreements (`ka_gochara`'s five-way split) and consumer-table
mismatches (`ka_tulana`, `ka_yojaka`, `ka_dasha_kala`) mean several assets cannot honestly be
called "qualified" even where data exists, independent of the empty-table problem.

**Third pattern:** the U01–U11 consumer-interface list under-names witness-tier Frontier assets
(6 of 9 have no U-id) and misses two genuinely-live Spine capabilities (`ka_avadhi`/
`ka_kala_darshana` via `kala_temporal.ts`) and the century materialiser entirely — the obligation
list itself has coverage gaps independent of asset-level readiness.

No asset in this matrix has any campaign event under the current definition `t3-2026-09-11-
8b884eac` — see `KALA_ACCEPTANCE_REGIME_MAPPING_v1_0.md` (T3) for why `Accepted N/22` is honestly
0/22 by two independent routes today.
