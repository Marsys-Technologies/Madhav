# T1 Traceability Matrix — Spine Cluster

Part 2 of 3 of T1 (Frontier / Spine / Kshetra+Century split). Read-only. Built on prior-cycle
inputs (F3 DAG reconciliation, F5 consumer-path trace, F7 data census, Domain F consumer
surfaces, T5 strategy tensions, F2 t3 campaign-event quantification) — none of that work is
redone here, only cited and synthesized.

## Cluster definition (how "Spine" was determined)

`00_ARCHITECTURE/briefs/nirmana/l3_autonomous/MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md` §4 ("The
three streams", lines 130–151) explicitly names three streams: **Stream A — Frontier (9 assets)**,
**Stream B — Spine (10 assets)**, **Stream C — Kshetra + Century (2 assets)**. Stream B's roster
(line 143–144):

> `avadhi`, `yojaka`, `gochara`, `sangam`, `kalasutra`, `vighnakara`, `taranga`, `kala_darshana`,
> `tulana`, `bhavishya_lekha`, `jivana_parva`

**Ambiguity flagged, not blocked on:** that line lists **11** names, but the section header says
"Spine (10 assets)" (line 142) — an internal off-by-one in the source document. I did not drop any
of the 11 to force a count of 10; per the task's instruction ("if in doubt about an asset's
cluster, include it here anyway and flag the ambiguity rather than dropping it"), all 11 are
covered below. Cross-checked against §3's dependency-tier table (lines 100–107): `yojaka` is
tier T0, `gochara`/`sangam` are T1/T2, `kalasutra`/`taranga`/`vighnakara` are T3, `kala_darshana`
is T4, `bhavishya_lekha`/`jivana_parva`/`tulana` are T5 — all 11 names resolve to real `ka_*`
identities (confirmed against `MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md` §6.1's A-nn rows and
`MADHAV_DATA_PLANE_ASSET_CONTRIBUTION_REGISTER_v2_0.md` §5), so none is a typo for a
Frontier/Kshetra asset. Final Spine roster (`ka_` prefix restored):

`ka_avadhi`, `ka_yojaka`, `ka_gochara`, `ka_sangam`, `ka_kalasutra`, `ka_vighnakara`, `ka_taranga`,
`ka_kala_darshana`, `ka_tulana`, `ka_bhavishya_lekha`, `ka_jivana_parva` — **11 assets.**

`ka_gochara_sweep` (protected, retired) is not part of any stream (elevation plan §4 only splits
the "residual 21" — actually 22 minus the assets already claimed elsewhere; the sweep sits outside
the active-DAG entirely per `MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md:293`, row `L3-H01`) — it is
Frontier/Kshetra/Spine-agnostic and not claimed here.

**F13/F14 ladder definitions used below** (`PROMPT_0_ENVIRONMENT_AND_ARCHITECTURE_AUDIT.md:110-112`):
- F13 (delivery/evidence): present → qualified → consumed → effect traceable → served → value evaluated
- F14/gate matrix §8: strategy agreed → producer ready → integrated → deployed → consumer value demonstrated → empirically evaluated

Three distinct axes are reported per asset, per the task's own framing that "code path exists ≠
campaign-event exists": **(a) code-present** (writer/consumer code exists), **(b)
canonical-chart-data-present** (F7 census row counts), **(c) campaign-event-present under t3**
(F2's per-asset ancestor-closure table — every one of these 11 assets shows **0 events under
`t3-2026-09-11-8b884eac`**, confirmed in `_work/F2.md`'s per-asset table). Ladder rungs below are
graded against whichever axis actually has evidence; where an axis has none, it says so rather
than defaulting to the more generous reading.

---

## Per-asset rows

### 1. `ka_avadhi`

- **Contribution-register disposition + DP obligations:** `P/E/I` — "Period dossiers with L1
  references... enrich qualified participant/condition context and share with chapters. DP08/10."
  (`MADHAV_DATA_PLANE_ASSET_CONTRIBUTION_REGISTER_v2_0.md:153`, source anchor `W/ka_avadhi.py:176`)
- **L3 strategy row + required transformation:** `L3-A12` — table `kala_avadhi`: chart × clock
  system × level × start, lords/dates/domain quality/citations. "Preserve clock hierarchy and
  actual interval identity; assess missing ayanamsha in the key, fixed domains, ten-row limits and
  soft-empty behavior. It reads L0/L1/L2, not Yojaka; Taranga currently does not read it."
  (`MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md:282`) — proposed eligibility W2.
- **L3-Q questions improved:** L3-Q01 ("what is active now, and why" — clocks/participants/
  condition, `STRAT:62`) and L3-Q06 ("how does this chapter differ from the preceding one" —
  avadhi is explicitly the clock/period substrate chapters draw on, `STRAT:67`). Judgment call —
  neither strategy row names avadhi by asset explicitly against a specific L3-Q; inferred from the
  A12 description's own language ("period dossiers", "clock hierarchy").
- **Product P-nn served:** via L3-Q01 → P09–10/P22; via L3-Q06 → P10 (`STRAT:62,67`).
- **Proving journey(s):** Financial-promise journey (§12.1) — the journey explicitly asks "which
  qualified clocks engage those same participants and conditions" for Window A/B comparison
  (`MADHAV_PRODUCT_DEFINITION_v3_0.md:433`) — avadhi's clock-hierarchy dossier is the natural
  supplier of that clock enumeration. Inferred, not asset-named in the journey text.
- **U-nn interface(s):** none of U01–U11 names avadhi explicitly (`_work/DOMAIN_F.md` U-table).
  Its actual live consumer is `kala_temporal.ts`'s `query_dasha_dossier` capability (see below),
  which is outside the numbered U-list — flagged as a possible **orphan obligation** (see below).
- **Receiving operator today:** `platform-mcp/src/tools/retrieval/kala_temporal.ts`,
  `query_dasha_dossier → kala_avadhi` (`DOMAIN_F.md:20`, header `kala_temporal.ts:1-28`) —
  classified **LIVE**, and explicitly documented as the fix that superseded the dead
  `kala_timeline.ts`/`kala_timeline` DARK pair (CR-40/T-1, 2026-07-16). Note: `kala_timeline.ts`
  itself is separately confirmed **DARK on three axes** (never registered on the MCP server; not
  whitelisted on the primitives route; no writer targets `kala_timeline`) while still claiming the
  same "KA-3-1 kala.timeline" asset id (`DOMAIN_F.md:19,20`) — a documentation/identity collision,
  not a functional gap for avadhi itself since `kala_temporal.ts` genuinely serves it.
- **F13/F14 ladder under t3:**
  - code-present: yes (writer `W/ka_avadhi.py:176`; consumer `kala_temporal.ts` wired and LIVE).
  - canonical-chart data: **1,169 rows**, single build timestamp 2026-08-12
    (`_work/F7.md:23`, table `kala_avadhi`).
  - campaign events under t3: **0** (2 ancestor defs w/ evidence — t1, t2 — neither reached
    `asset_frozen`; `_work/F2.md` line 108).
  - **F13:** present (code+data) → plausibly consumed (LIVE wiring, non-trivial row count) →
    **served COULD NOT VERIFY** (no end-to-end response-payload trace done this pass) → effect
    traceable/value evaluated: no evidence found, not reached.
  - **F14:** strategy agreed (yes — `APPROVED_STRATEGY` doc §6.1 row A12) → producer ready (yes,
    data exists) → integrated (yes, live consumer reads it) → deployed/consumer value
    demonstrated/empirically evaluated: **no D9/D10 evidence found**, not reached.

### 2. `ka_yojaka`

- **Disposition + DP:** `P/E/I/Q/C` — "Typed activation predicates and fired-yoga participant
  lookup... full mechanism compiler; preserve paired CDLM signals/roles and method key, not net
  domain average. DP05/06/08." (`CONTRIB_REG:147`, anchor `W/ka_yojaka.py:479-510`)
- **Strategy row + transformation:** `L3-A11` — table `kala_activation_predicates`: chart ×
  ayanamsha × signal × predicate signature, eligibility/trigger/strength payloads. "Compile
  complete accepted L2 mechanisms, participants, signed multidomain relations, cancellation and all
  linked roots. Remove one-domain/five-link flattening with explicit migration... **79 unmatched
  MSR references** must resolve." (`STRAT:281`; MSR-ref figure independently re-confirmed in
  `_work/F7.md` §4a: 79 of 50,678 rows, 0.156%, do not resolve against `bodha_msr_signals`.)
- **L3-Q improved:** L3-Q03 ("does a named configuration have a complete activation route" —
  formation/cancellation/participants/rival routes, `STRAT:64`) — direct match, yojaka is the
  mechanism compiler. Also L3-Q01 (what's active now — yojaka's predicates are inputs to activation
  state).
- **P-nn served:** via L3-Q03 → P09; via L3-Q01 → P09–10/P22.
- **Proving journey(s):** NBRY journey (§12.2) — "Check the actual formation, cancellation
  condition and further qualifications... List eligible activation routes" (`PRODUCT_DEF:439,441`)
  is exactly what a mechanism/activation-predicate compiler supplies. Financial-promise journey
  (§12.1) also depends on "applicable configurations and their cancellations."
- **U-nn interface(s):** **U01** — "L2→Yojaka/Kshetra binding (producer fields, generations,
  signed routes)" (`DOMAIN_F.md:50`) names Yojaka explicitly: "Y — `ka_kshetra`/`ka_yojaka` served
  via `kala_views/{ahead,priority,ritual,story}.ts` per F5."
- **Receiving operator today:** F5 lists two: `.../L3_kala/query_temporal_activation.ts` (asset_id
  in header only, **low-medium confidence**, target table not independently verified —
  `_work/F5.md:49`) and the `kala_views/{ahead,priority,ritual,story}.ts` family (asset_id
  co-occurrence, table not independently re-verified — `DOMAIN_F.md:23`). Neither trace confirms
  the consumer actually reads `kala_activation_predicates` (yojaka's own table) rather than a
  neighboring table — this is a **real, flagged gap**, same class as the confirmed `ka_tulana`/
  `ka_dasha_kala` divergences, just not yet promoted to CONFIRMED because F5's own confidence
  rating for this row is low-medium, not a negative finding.
- **F13/F14 ladder:**
  - code-present: yes.
  - canonical-chart data: `kala_activation_predicates` = **50,678 rows** (`F7.md:22`) — largest
    populated table in the cluster besides `kala_field` (Kshetra, not Spine).
  - campaign events under t3: **0** (2 ancestor defs — t1, t2 — **did** reach `asset_frozen` under
    t2, per `F2.md:129`, but that is a superseded generation, inadmissible under t3 per F2's own
    Option-A/B analysis).
  - **F13:** present (strong data) → **qualified COULD NOT VERIFY** (79-row MSR-ref gap is exactly
    the kind of defect that blocks qualification per D1/D4 — register itself still carries an
    open `Q` disposition) → consumed: **low-medium confidence only**, table-level read not
    independently confirmed → served/effect-traceable/value-evaluated: not reached.
  - **F14:** strategy agreed (yes, A11) → producer ready (yes, 50,678 rows) → integrated:
    low-medium confidence only (see above) → deployed/consumer-value/empirical: not reached.

### 3. `ka_gochara`

- **Disposition + DP:** `P/I/Q` — "Contact/search numerics and generation-bearing
  materialization... separate service/writer/coverage from interpretive conclusion; preserve
  protected data contracts. DP07/08." (`CONTRIB_REG:139`, anchor `W/ka_gochara.py:180`)
- **Strategy row + transformation:** `L3-A13` — table `kala_gochara_windows_v2`, generation 2.0:
  chart/class/shape/window, signed terms/valence/suppression. "Preserve v2 computation and
  progressive roughly ±3-year search as bounded coverage... Materialized v2 rows are not Sangam's
  current transit input." (`STRAT:283`) — proposed eligibility W3.
- **L3-Q improved:** L3-Q01 (what's active now — transit contact) and L3-Q08 (is no window found a
  real negative — the strategy row's own "bounded ±3-year search" language is precisely L3-Q08's
  "searched horizon, resolution... unavailable inputs" concern, `STRAT:69`).
- **P-nn served:** via L3-Q01 → P09–10/P22; via L3-Q08 → P09/P16/P18.
- **Proving journey(s):** no direct citation found; transit-contact windows are load-bearing for
  both Financial-promise (§12.1, "which qualified clocks engage") and NBRY (§12.2, "closest
  contact") journeys, but the DIVERGENT finding below means this participation is currently at
  risk of being **wrong data**, not just under-evidenced.
- **U-nn interface(s):** not directly named in U01–U11's text, but DOMAIN_F's summary explicitly
  ties the identity-collision finding to `kala_ahead_get`'s "ka_gochara-sourced rows"
  (`DOMAIN_F.md:26`) — bearing on U06/U09 territory (promise-spine/AHEAD projections) without a
  clean U-id match.
- **Receiving operator today:** `platform-mcp/src/tools/retrieval/register_gochara_windows.ts` —
  classified **DIVERGENT (real finding)**, both in F5 and independently corroborated by T5's
  Tension 1 as a **five-way** disagreement, not the three-way the audit brief originally expected:
  STRAT + WRITER CODE + a migration all agree the writer's table is `kala_gochara_windows_v2`
  gen `2.0`; SEED-TS + the LIVE CONSUMER (`register_gochara_windows.ts:581`) both point at the
  un-suffixed `kala_gochara_windows` gen `3.0` instead (`T5.md:18-46`). T5 additionally finds
  (§Tension 7, `T5.md:238-269`) that `ka_sangam`'s declared `depends_on: ka_gochara` edge resolves
  in code to a **different asset that shares the name** (`services/ka_gochara/service.py`, a
  distinct pre-existing `service`-kind asset retained as a backward-compat alias) — so even the
  DAG edge feeding off this asset is hollow.
- **F13/F14 ladder:**
  - code-present: yes, but split-identity (two tables, two generations both live).
  - canonical-chart data: writer's own table `kala_gochara_windows_v2` = **1,001 rows**
    (generations `g3_utkarsha`=914, `2.0`=87 — `F7.md:50,96`); the table the consumer actually
    cites, `kala_gochara_windows`, = **17,211 rows** (`F7.md:47`) — but per the DIVERGENT finding
    those are not confirmed to be the current writer's own output.
  - campaign events under t3: **0** (1 ancestor def, t1, **did** reach `asset_frozen` there —
    `F2.md:111` — superseded, inadmissible under t3).
  - **F13:** present (code+data both exist, on two tables) → qualified: **blocked** — a
    table-identity defect this severe (five-way source disagreement) means the asset cannot
    honestly be called "qualified" until STRAT/WRITER/SEED/LIVE CONSUMER converge on one
    table+generation → consumed/served/effect-traceable/value-evaluated: not reachable while
    qualified is blocked.
  - **F14:** strategy agreed (yes, A13, though STRAT's own table claim is one side of the
    disagreement) → producer ready: yes on its own declared table, but the "which table is real"
    question undermines a clean yes → integrated/deployed/consumer-value/empirical: not reached.

### 4. `ka_sangam`

- **Disposition + DP:** `P/E/I/Q` — "Targeted/exploratory convergence and contact search...
  consume full configuration/domains/conditions, not first domain or missing-dignity 0.5. DP06/08."
  (`CONTRIB_REG:148`, anchor `W/ka_sangam.py:331-377`)
- **Strategy row + transformation:** `L3-A15`, Tier S ("the three hard ones") — table
  `kala_convergence`: chart/signal/mode/window, score/orb/rarity/constituents; "one domain and
  missing ayanamsha identity need review... **The chokepoint — 7 of 21 depend on it**... Remove
  hidden coverage caps and default independent-witness claims." (`STRAT:285`;
  `MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md:64`) — proposed eligibility W3.
- **L3-Q improved:** L3-Q07 ("which domains interact over time" — qualified structural linkage,
  coincident intervals, `STRAT:68`) and L3-Q04 ("why can activity coexist with strain" —
  overlapping support/inhibition paths, `STRAT:65`) — both inferred from sangam's role as the
  shared convergence substrate for downstream integrators (T5 confirms 5 of 8 integrators descend
  from it, `T5.md:227-230`).
- **P-nn served:** via L3-Q07 → P01/P03–10/P17; via L3-Q04 → P03–04.
- **Proving journey(s):** both Financial-promise (§12.1, "qualified structural relationships") and
  NBRY (§12.2, "eligible activation routes... opposing conditions") journeys structurally depend
  on convergence — but T5's Tension 4 (`T5.md:144-171`) finds the register's own named defects
  ("first domain", "missing-dignity 0.5") are **still present in code**, unlike the analogous
  defect in `ka_kala_darshana` which was partly fixed — so participation today risks the same
  flattening the register itself warns against.
- **U-nn interface(s):** not directly named in U01-U11's text. Its reach is indirect but total:
  per T5 (`T5.md:227-230`), `ka_sangam` is "the common ancestor of five of the eight integrators"
  — any U-item touching `ka_kala_darshana`, `ka_vighnakara` (U03), `ka_bhavishya_lekha`,
  `ka_jivana_parva`, or `ka_taranga` is transitively reading sangam's output presented as if
  independently corroborating.
- **Receiving operator today:** `.../L3_kala/query_convergence_windows.ts`;
  `query_temporal_activation.ts`; `kala_views/ahead.ts` (medium confidence, `F5.md:55`).
- **F13/F14 ladder — the most significant single finding in this cluster:**
  - code-present: yes, and extensively wired (7 declared dependents, chokepoint role confirmed).
  - **canonical-chart data: `kala_convergence` = 0 rows for the canonical chart**
    (`F7.md:25` — "Globally non-empty (20,497 rows across 2 other charts)"). Sangam's own table
    has **never been populated for the canonical chart `482012f1-…`** despite being described in
    the elevation plan as "THE VALUABLE CORE".
  - campaign events under t3: **0**; F3's own §4 finding independently corroborates this from the
    build-manifest side: of 23 identities, `ka_sangam` is one of 12 that has **never been
    dispatched through a run whose manifest survived**, "despite 522 build_runs existing for the
    canonical chart" (`KALA_DAG_RECONCILIATION_v1_0.md:51-60`).
  - **F13: present is the honest ceiling.** Code exists; canonical-chart data does not. Qualified/
    consumed/served/effect-traceable/value-evaluated are all **unreachable, not merely unverified**
    — there is nothing in `kala_convergence` for this chart to consume, serve, or evaluate.
  - **F14: strategy agreed only.** Producer ready is **NO** for the canonical chart specifically
    (0 rows) — this directly contradicts any reading that treats sangam's "medium confidence"
    consumer-wiring (F5) as evidence of readiness; wiring without data is not readiness.

### 5. `ka_kalasutra`

- **Disposition + DP:** `P/E/I/Q/C` — "Deterministic interval resolution and recurrence... shared
  interval kernel with exact peak/horizon/truncation semantics; best-score selection is not
  nearest search. DP07/08." (`CONTRIB_REG:149`, anchors `W/ka_kalasutra.py:66-116`,
  `S/ka_temporal/date_resolver.py:417-588`)
- **Strategy row + transformation:** `L3-A16` — table `kala_activation`: chart × signal ×
  ayanamsha × period, period-ID arrays and resolved windows/peaks. "Preserve useful timeline
  cache/batching. Retain all qualified recurrences and multiple convergence contributions; remove
  default-eight truncation, implicit today and redundant payloads through explicit consumer
  migration." (`STRAT:286`) — proposed eligibility W4.
- **L3-Q improved:** L3-Q02 ("when is the closest eligible window, and which later window is
  better supported" — nearest/strongest/robust distinctions, `STRAT:63`) — direct match, kalasutra
  is explicitly the interval/peak/horizon resolver.
- **P-nn served:** via L3-Q02 → P03–04/P09.
- **Proving journey(s):** Financial-promise (§12.1, "Window A might support nearer activity...
  Window B might have more coherent support") and NBRY (§12.2, "closest contact, better-supported
  windows") — kalasutra's own job description is a near-literal match for both journeys' Window
  A/B mechanics.
- **U-nn interface(s):** **U04** — "Kalasutra/Tulana→AHEAD/NOW (nearest future recurrence,
  coverage)" names kalasutra explicitly, rated **Y, with a known gap** (the gap is on the Tulana
  half, not Kalasutra's — `DOMAIN_F.md:53`).
- **Receiving operator today:** `.../L3_kala/query_temporal_activation.ts`; `kala_views/ahead.ts`,
  `now.ts` — **high confidence**, F5 states it "reads writer's own `kala_activation` table plus a
  documented L2 join" (`F5.md:61`).
- **F13/F14 ladder — second major finding:**
  - code-present: yes, high-confidence wiring to its own declared table.
  - **canonical-chart data: `kala_activation` = 0 rows for the canonical chart**
    (`F7.md:21` — "Globally non-empty (337,148 rows) but **100% owned by other charts**"). Despite
    F5's "high confidence" same-table verdict, there is nothing in that table for this chart.
  - campaign events under t3: **0**; and per F2, `ka_kalasutra` is one of only **3 assets with
    zero campaign evidence in any generation, ever** (`F2.md:147-150`) — no ancestor, no t3,
    nothing (the other two are `ka_gochara_v` and `ka_vighnakara`, both Spine or Frontier-adjacent
    per §5/§6 below).
  - **F13: present ceiling only**, same class of gap as `ka_sangam` — high-confidence code wiring
    to an empty table is not evidence of consumption, service, or value; it is evidence the wiring
    is correct and the data pipeline has not run for this chart.
  - **F14: strategy agreed only.** Never analyzed under any campaign definition; producer ready is
    **NO** for the canonical chart.

### 6. `ka_vighnakara`

- **Disposition + DP:** `P/I/Q` — "Explicit counter-indicator interface and astronomical calls...
  qualify detector, target and interval; distinguish one underlying obstruction from repeated
  representation. DP08." (`CONTRIB_REG:150`, anchor `W/ka_vighnakara.py:144`)
- **Strategy row + transformation:** `L3-A17` — table `kala_obstruction`: chart/signal/optional
  convergence, kind/severity/override/roots. "Preserve opposition separately from activity.
  Resolve top-500 coverage, null-convergence association, deterministic ties, targeted
  applicability and duplicated roots; no absence-of-evaluation as clear passage." (`STRAT:287`) —
  proposed eligibility W4.
- **L3-Q improved:** L3-Q04 ("why can activity coexist with strain" — inhibiting paths overlapping
  supporting paths, `STRAT:65`) — direct match, vighnakara is the explicit counter-indicator layer.
- **P-nn served:** via L3-Q04 → P03–04.
- **Proving journey(s):** Financial-promise (§12.1, "counter-evidence that distinguishes obtaining
  resources from keeping them... unresolved retention constraint") and NBRY (§12.2, "opposing
  conditions with scope and uncertainty") — both journeys explicitly need an obstruction/
  counter-evidence layer, which is vighnakara's stated job.
- **U-nn interface(s):** **U03** — "Vedha/TRIGGER/Vighnakara→integrators (persist obstruction
  target/role/interval/source/state)" names vighnakara explicitly, rated **Y**
  (`DOMAIN_F.md:52`).
- **Receiving operator today:** `.../L3_kala/query_obstruction_periods.ts` — **high confidence**,
  `FROM kala_obstruction` direct table read (`F5.md:59`).
- **F13/F14 ladder:**
  - code-present: yes, high-confidence direct table read.
  - **canonical-chart data: `kala_obstruction` = 0 rows for the canonical chart**
    (`F7.md:55` — "Globally non-empty (747 rows across 2 other charts)"). Third instance of the
    same pattern (high-confidence wiring, empty table).
  - campaign events under t3: **0**; also one of the **3 zero-campaign-evidence-ever assets**
    alongside `ka_kalasutra` (`F2.md:128,147-150`).
  - **F13: present ceiling.** T5's Tension 5 corroborates independently: `ka_kala_darshana`'s net
    score composes `ka_sangam` with `ka_vighnakara` obstructions, but per F3 `ka_vighnakara`'s own
    LIVE deps include `ka_sangam` — "so 'convergence × obstruction' is not two independent
    readings; both legs descend from `ka_sangam`" (`T5.md:219`). Even once data exists, the
    presentation-layer independence the register calls for (DP08) is not yet structurally true.
  - **F14: strategy agreed only.** Producer ready is **NO** for the canonical chart.

### 7. `ka_taranga`

- **Disposition + DP:** `P/I/Q/C` — "Coarse multiresolution trend projection... candidate
  projection of common qualified evidence; current grade/convergence averaging is not event
  probability. DP08/10." (`CONTRIB_REG:152`, anchor `W/ka_taranga.py:120-170`)
- **Strategy row + transformation:** `L3-A18` — table `kala_taranga`: chart × month × scope
  kind/ID over 1950-2100. "Preserve timeline signal; inspect raw Mahadasha context/ayanamsha and
  class-specific meaning. Class dasha can degenerate to shared domain behavior and class transit
  to domain maxima. Use actual Pratijna/convergence/clocks/ontology; no invented Avadhi
  dependency." (`STRAT:288`) — proposed eligibility W4.
- **L3-Q improved:** L3-Q06 (how this chapter differs — trend projection over a long horizon,
  `STRAT:67`) and L3-Q02 (nearest/strongest window — trend as a candidate-projection signal,
  `STRAT:63`).
- **P-nn served:** via L3-Q06 → P10; via L3-Q02 → P03–04/P09.
- **Proving journey(s):** no direct citation; a long-horizon trend signal is plausible supporting
  evidence for the Financial-promise journey's "nearer activity vs sustained outcome" distinction
  (§12.1) but this is inferred, not asset-named in the journey text.
- **U-nn interface(s):** not named in U01–U11.
- **Receiving operator today:** `.../L3_kala/query_activation_waveform.ts` — medium confidence
  (`F5.md:53`).
- **F13/F14 ladder:**
  - code-present: yes.
  - **canonical-chart data: `kala_taranga` = 92,412 rows** (`F7.md:58`), single build timestamp
    2026-08-13 — one of only two Spine assets (with `ka_jivana_parva`) that is both wired and
    genuinely populated for the canonical chart.
  - campaign events under t3: **0** (1 ancestor def, t2, did not reach `asset_frozen` —
    `F2.md:124`).
  - **F13:** present (strong data) → consumed: medium confidence (asset_id + header citation only,
    table read not independently re-verified — `F5.md:53`) → **qualified is blocked** by T5's
    Tension 6 finding: `ka_taranga` averages `kala_convergence` (from `ka_sangam`, itself enriched
    from `bodha_msr_signals`) with `bodha_pratijna` (same L2 Bodha substrate) — "the average reads
    as corroboration between two views of one source" (`T5.md:220`), which is exactly the
    "grade/convergence averaging is not event probability" defect the register already names
    (DP08/10). Served/effect-traceable/value-evaluated: not reached.
  - **F14:** strategy agreed (yes, A18) → producer ready (yes, real data) → integrated: medium
    confidence only → deployed/consumer-value/empirical: not reached.

### 8. `ka_kala_darshana`

- **Disposition + DP:** `P/I/Q/C` — "Convergence/obstruction presentation join... qualify
  independent net-score authority; global top-750 and NULL→0.5 are not complete personalized
  search. DP08/10/12." (`CONTRIB_REG:155`, anchor `W/ka_kala_darshana.py:21-33,85-102`)
- **Strategy row + transformation:** `L3-A19` — table `kala_darshana`: chart/convergence/signal/
  window, effective score and obstruction summary. "Preserve the zero-handling repair; resolve
  top-750 truncation and missing-convergence 0.5 default... Current computation reads
  convergence/obstruction, **not** `kala_activation` as the registry claims."
  (`STRAT:289`) — proposed eligibility W5.
- **L3-Q improved:** L3-Q01 (what's active now and why — the darshana row is literally a
  convergence+obstruction presentation join, `STRAT:62`).
- **P-nn served:** via L3-Q01 → P09–10/P22.
- **Proving journey(s):** Financial-promise/NBRY journeys both need a combined
  "presence+opposition" verdict, which darshana is designed to supply — but see the independence
  defect below.
- **U-nn interface(s):** not named directly in U01–U11, but this is the same asset DOMAIN_F
  identifies as genuinely serving the "KA-3-1 kala.timeline" designation via `kala_temporal.ts`'s
  `query_temporal_view → kala_darshana` (`DOMAIN_F.md:20`) — i.e. it inherits the asset-id
  collision discussed under `ka_avadhi` above (both are legitimate halves of the same disputed
  "kala.timeline" label; `ka_avadhi` via `query_dasha_dossier`, `ka_kala_darshana` via
  `query_temporal_view`).
- **Receiving operator today:** `.../L3_kala/query_temporal_view.ts` (medium confidence, `F5.md:50`)
  and confirmed as the genuinely-LIVE half of `kala_temporal.ts` per `DOMAIN_F.md:20`.
- **F13/F14 ladder:**
  - code-present: yes, and confirmed LIVE (not dark) via `kala_temporal.ts`.
  - **canonical-chart data: `kala_darshana` = 0 rows for the canonical chart**
    (`F7.md:27` — "Globally non-empty (750 rows), all owned by chart `1c826d5a-…`"). Fourth
    instance of the wired-but-empty pattern.
  - campaign events under t3: **0** (1 ancestor def, t2, did not reach `asset_frozen` —
    `F2.md:116`).
  - **F13: present ceiling**, same class as sangam/kalasutra/vighnakara — a genuinely LIVE,
    correctly-wired consumer surface with zero canonical-chart rows to serve. T5's Tension 5 adds
    an independent qualification defect even once data exists: darshana's net score composes
    `ka_sangam` (via `kala_convergence`) with `ka_vighnakara`'s obstructions, but `ka_vighnakara`
    itself reads `ka_sangam` — "both legs descend from `ka_sangam`" (`T5.md:219`), directly
    matching the register's own "qualify independent net-score authority" flag.
  - **F14: strategy agreed only.** Producer ready is **NO** for the canonical chart, despite being
    one of the few genuinely-LIVE (not dark) wiring cases in this cluster.

### 9. `ka_tulana`

- **Disposition + DP:** `P/I/Q` — "Comparison service and factor breakdown... compare named
  outcomes/criteria, nearest/strongest/robust separately; self-test not consumer-value proof.
  DP08/17." (`CONTRIB_REG:157`, anchor `S/ka_tulana/writer.py; service.py`)
- **Strategy row + transformation:** `L3-A04` — "Pure `WindowInput` comparison service; synthetic
  probe, zero rows... Preserve useful ranking kernel; add matched mechanism/context, nearest
  versus stronger/robust candidates, trade-offs, ties and incomparable states. Prove both pure
  behavior and accepted-window use." (`STRAT:274`) — proposed eligibility W2 pure / W7 data-bound.
- **L3-Q improved:** L3-Q02 explicitly — "when is the closest eligible window, and which later
  window is better supported" (`STRAT:63`); this is a near-literal restatement of tulana's own
  disposition text ("nearest/strongest/robust separately").
- **P-nn served:** via L3-Q02 → P03–04/P09.
- **Proving journey(s):** Financial-promise (§12.1, explicit Window A/B comparison) and NBRY
  (§12.2, "closest contact" vs "better-supported windows") — tulana's ranking kernel is the most
  directly-named comparison mechanism for both journeys' core "nearest vs strongest" question.
- **U-nn interface(s):** **U04** — "Kalasutra/Tulana→AHEAD/NOW", rated **Y, with a known gap**:
  "per F5, `ka_tulana`'s consumer wrapper reads `kala_activation` (owned by `ka_kalasutra`), not
  any table traceable to `ka_tulana`'s own writer — so the 'Tulana' half of this U-item has an
  open §N.8-flagged gap even though the tool itself is callable." (`DOMAIN_F.md:53`)
- **Receiving operator today:** `call_service_wrappers.ts` (`call_priority_ranking`);
  `kala_views/priority.ts`; `register_p1_aliases.ts` — classified **NOT-FOUND (real finding)** by
  F5: the consumer's SQL selects from `kala_activation` (a table `ka_kalasutra` owns), and
  `grep target_table|INSERT INTO` on `ka_tulana/writer.py` found **zero hits** (`F5.md:65`).
  Independently corroborated this pass: **no `kala_tulana` table exists anywhere in F7's 37-table
  census** (`F7.md` table list, §1) — consistent with the strategy doc's own "synthetic probe, zero
  rows" description (`STRAT:274`). F5 leaves this genuinely open (low confidence, "could not
  confirm within budget whether `ka_tulana` co-writes `kala_activation` by design, or the consumer
  silently substitutes a neighbor's data").
- **F13/F14 ladder:**
  - code-present: yes (service exists, callable).
  - canonical-chart data: **no table exists to hold any** — consistent with `ka_tulana` being a
    pure, stateless comparison service by design (per STRAT), not a writer with a physical table.
    This changes the reading of "present": if pure-service-by-design is the correct interpretation,
    "present" should be graded on service callability, not row count — but if the consumer's
    `kala_activation` read is instead an undisclosed substitution (F5's unresolved alternative),
    "present" for tulana's *own* output is currently **false**, full stop.
  - campaign events under t3: **0** (1 ancestor def, t2, **did** reach `asset_frozen` there —
    `F2.md:126` — superseded, inadmissible under t3).
  - **F13:** present is **ambiguous by design vs defect**, not merely unverified — this is the
    sharpest of the "not guessed at" cases the source packets flag. Consumed/served/effect
    traceable/value evaluated: not reachable until the ambiguity resolves.
  - **F14:** strategy agreed (yes, A04, and the strategy doc's own "pure vs data-bound" split
    anticipates exactly this ambiguity) → producer ready: **undetermined by design** → integrated:
    the tool is callable (some integration), but into which table is unresolved → deployed/
    consumer-value/empirical: not reached.

### 10. `ka_bhavishya_lekha`

- **Disposition + DP:** `P/I/Q/C` — "Forward packaging and historical outcome references...
  shared qualified selection/claim boundary; top-100/five-year filter is not exhaustive future
  coverage; historical purpose isolated. DP08/12/15." (`CONTRIB_REG:156`, anchor
  `W/ka_bhavishya_lekha.py:24-115`)
- **Strategy row + transformation:** `L3-A21` — table `kala_bhavishya`: chart × rank, tier/domain/
  window/falsifier/source plus retained outcomes. "Preserve projection usefulness and
  observations. Replace unstable rank identity; fix empty-input deletion path first. Declare
  five-year/top-100 scope, full source identity and non-probability meaning; rebuildable
  projections cannot own or rewrite issued history." (`STRAT:291`) — proposed eligibility W6
  after preservation gate.
- **L3-Q improved:** L3-Q08 (is no window found a real negative — five-year/top-100 scope
  disclosure, `STRAT:69`) and L3-Q11 (what do actual observations fit or fail to fit — retained
  outcomes/historical references, `STRAT:72`).
- **P-nn served:** via L3-Q08 → P09/P16/P18; via L3-Q11 → P12/P20.
- **Proving journey(s):** **Historical-challenge journey (§12.3) — direct, not inferred.** "You
  predicted a promotion. It did not happen." requires retrieving "the original completed reading
  and frozen claim" (`PRODUCT_DEF:445`) — this is precisely `ka_bhavishya_lekha`'s stated job
  ("preserve issued claims, outcomes and referrers... rebuildable projections cannot own or
  rewrite issued history"). Also participates in Financial-promise (§12.1) via its forward
  packaging role.
- **U-nn interface(s):** **U06** ("Qualified stages→PACT/promise spine") via `kala_views/ahead.ts`
  which F5 confirms reads the `ka_kshetra`/`ka_yojaka`/`ka_bhavishya_lekha` family
  (`F5.md:47,56`); and **U09** ("Historical comparison→prospective firewall — AHEAD echoes stay out
  of historical rows") is conceptually this asset's exact job (separating retained outcomes from
  prospective forecast) though DOMAIN_F rates U09 itself as "Y (tool exists), firewall logic
  COULD NOT VERIFY" (`DOMAIN_F.md:58`) — not independently re-checked this pass.
- **Receiving operator today:** `.../L3_kala/query_projections.ts`; `kala_views/ahead.ts` —
  medium confidence (`F5.md:47`).
- **F13/F14 ladder:**
  - code-present: yes.
  - **canonical-chart data: `kala_bhavishya` = 0 rows for the canonical chart**
    (`F7.md:24` — "Globally non-empty (100 rows), all owned by chart `1c826d5a-…`"). Fifth
    instance of the wired-but-empty pattern, and the most consequential given this is the asset
    specifically responsible for D7 history-safety (issued claims must survive rebuild) — with
    zero canonical-chart rows, there is currently no issued-claim history for this chart to
    protect or violate.
  - campaign events under t3: **0** (1 ancestor def, t2, did not reach `asset_frozen` —
    `F2.md:109`).
  - **F13: present ceiling.** T5's Tension 6 (`T5.md:221`) adds a further qualification defect on
    top of the empty-table finding: even once populated, three of `bhavishya_lekha`'s four
    declared inputs trace to one producer (`ka_sangam`, directly and via `ka_kala_darshana` and
    `ka_vighnakara`) — a "triple-count risk" — plus the confirmed-present `LIMIT 100` /
    five-year-window truncation the register already names.
  - **F14: strategy agreed only.** Producer ready is **NO** for the canonical chart.

### 11. `ka_jivana_parva`

- **Disposition + DP:** `P/E/I/Q` — "Chapter hierarchy, birth clipping and references... current
  fine-period scope is running AD; enrich mechanisms rather than generic keywords; disclose
  coverage. DP08/10." (`CONTRIB_REG:154`, anchor `W/ka_jivana_parva.py:53`)
- **Strategy row + transformation:** `L3-A20` — table `kala_jivana_parva`: chart × level/index,
  year bounds/lord/theme/class. "Preserve chapter hierarchy but retain exact interval/clock/
  context and mechanism links. Replace unordered predicate `LIMIT 1` selection with a qualified
  relation; distinguish prior/later chapter changes and all relevant domain interactions."
  (`STRAT:290`) — proposed eligibility W6.
- **L3-Q improved:** L3-Q06 explicitly — "how does this chapter differ from the preceding one" —
  near-literal match, `STRAT:67`.
- **P-nn served:** via L3-Q06 → P10.
- **Proving journey(s):** no direct citation to §12.1–12.3, but chapter-level narrative context
  plausibly supports all three (each journey situates its answer within "what chapter" the person
  is in) — inferred, not asset-named.
- **U-nn interface(s):** not named in U01–U11.
- **Receiving operator today:** `.../L3_kala/query_life_arc.ts`; `kala_views/story.ts` —
  medium-high confidence, "asset_id in dedicated query file + narrative surface" (`F5.md:52`);
  `register_p1_synthesis.ts`'s `kala_life_arc_get` confirmed LIVE and traced to `query_life_arc.ts`
  → `ka_jivana_parva` (`DOMAIN_F.md:18`).
- **F13/F14 ladder:**
  - code-present: yes, LIVE, confirmed registration (`register_p1_synthesis.ts:726-764`).
  - **canonical-chart data: `kala_jivana_parva` = 100 rows** (`F7.md:52`), single build timestamp
    2026-08-13 — the second (with `ka_taranga`) genuinely wired-and-populated Spine asset.
  - campaign events under t3: **0** (1 ancestor def, t2, did not reach `asset_frozen` —
    `F2.md:115`).
  - **F13:** present (data exists) → consumed: medium-high confidence, confirmed LIVE tool
    registration → **qualified is blocked** by T5's Tension 6: `ka_jivana_parva`'s declared
    inputs include `ka_kala_darshana` (itself a `ka_sangam` composite) and `ka_sangam` directly —
    "chapter-level narrative agreement across these is agreement with `ka_sangam`, restated"
    (`T5.md:222`). Served/effect-traceable/value-evaluated: not reached.
  - **F14:** strategy agreed (yes, A20) → producer ready (yes, real data + LIVE registration) →
    integrated (yes, medium-high confidence) → deployed/consumer-value/empirical: no D9/D10
    evidence found, not reached.

---

## Orphan obligations found in this cluster

1. **`ka_avadhi` and `ka_kala_darshana` both genuinely serve the "kala.timeline"/"KA-3-1" asset
   label via `kala_temporal.ts`, but no U-nn item names either of them.** DOMAIN_F's U01–U11 table
   is built directly off the strategy doc's own U-list (`STRAT:441-451`), and neither U-item covers
   the clock-dossier/darshana-presentation pair that `kala_temporal.ts` actually serves — this is
   an obligation (a genuinely-live consumer capability) with no owning U-id, not a missing asset.
2. **The `ka_yojaka` consumer-table binding has no confirmed owner.** F5 rates the
   `query_temporal_activation.ts` binding "low-medium confidence... table not verified"
   (`F5.md:49`). If `ka_yojaka`'s own `kala_activation_predicates` table is not what that consumer
   actually reads, `ka_yojaka` joins `ka_tulana`/`ka_dasha_kala` as a third asset whose own output
   may not reach any confirmed consumer — an obligation (D8 consumer integration) with no verified
   discharge.
3. **No campaign-event vocabulary exists for `CONSUMER_INTEGRATED` or `VALUE_EVALUATED`** for any
   of these 11 assets (confirmed by F2's query 6: the L3 event-type list has no such entry). This
   is a cluster-spanning orphan obligation, not asset-specific: D8/D10-shaped acceptance criteria
   exist in the strategy (§6.1 for every A-nn row above) with no receipt mechanism to ever satisfy
   them under the current campaign-event schema.

## Orphan work found in this cluster

1. **`ka_taranga`'s and `ka_jivana_parva`'s writers have run and hold genuine canonical-chart
   data (92,412 and 100 rows respectively) with live, registered consumers — yet neither shows any
   campaign event under t3, and neither reached `asset_frozen` even in an ancestor generation**
   (`F2.md:115,124`). This is real, working, served-eligible output with no campaign receipt
   recording it — work that exists but is invisible to the `Accepted N/22` headline metric as
   currently instrumented.
2. **`ka_sangam`, `ka_kalasutra`, `ka_vighnakara`, `ka_kala_darshana`, `ka_bhavishya_lekha` all
   carry live or near-live consumer-surface wiring (medium-to-high F5 confidence, in three cases —
   `kalasutra`, `vighnakara`, `kala_darshana` — independently confirmed LIVE) aimed at tables that
   hold zero rows for the canonical chart.** This is the inverse of orphan work — wiring effort
   spent with no data behind it yet — worth naming as a distinct failure mode from both "orphan
   obligation" (missing owner) and ordinary "orphan work" (unserved obligation): call it **wired
   orphan capacity** — the receiving operator is built and would work the moment the writer runs
   for this chart, but nothing has triggered that run. Given `ka_sangam`'s chokepoint role (7 of 21
   declared dependents), this is very likely the single highest-leverage fix available in the
   Spine cluster.
3. **`ka_gochara`'s writer output (`kala_gochara_windows_v2`, 1,001 canonical-chart rows) and the
   separately-populated `kala_gochara_windows` (17,211 rows) both exist and both have live
   consumer code pointed at them** — but per the DIVERGENT finding, only one can be the actual
   current writer's output. Whichever table the consumer is NOT correctly reading is, by
   definition, orphan work: real data, real writer effort, with its own designated consumer
   pointed elsewhere.
