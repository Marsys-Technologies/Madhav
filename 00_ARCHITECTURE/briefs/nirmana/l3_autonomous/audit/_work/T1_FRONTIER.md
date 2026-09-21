# T1 Traceability Matrix — Frontier Cluster

**Part 1 of 3 of T1** (Frontier / Spine / Kshetra+Century split). Produced read-only, budget-capped
(~30 tool calls used of a 45 ceiling). Builds on prior-cycle inputs — does not redo their work,
cites and extends.

## Cluster definition (how "Frontier" was determined)

`00_ARCHITECTURE/briefs/nirmana/l3_autonomous/MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md` §4 ("The
three streams") names the split explicitly and unambiguously — no judgment call was needed:

> **Stream A — Frontier (9 assets)** (line 134): `graha_sancara`, `dasha_kala`, `muhurta_seva`,
> `gochara_resonance`, `kota_chakra`, `moorti_nirnaya`, `sudarshana_varsha`, `tithi_pravesha`,
> `vedha_gochara`. "All T0. Owns hubs `ka_graha_sancara`, `ka_dasha_kala`, `ka_muhurta_seva`,
> `ka_gochara_resonance`, `gochara_grammar`, `gochara_intensity`. **Upstream of both other
> streams — must run first and fastest.**" (lines 137–140)
>
> Contrast: **Stream B — Spine (10 assets)**: `avadhi`, `yojaka`, `gochara`, `sangam`, `kalasutra`,
> `vighnakara`, `taranga`, `kala_darshana`, `tulana`, `bhavishya_lekha`, `jivana_parva` (lines
> 142–143). **Stream C — Kshetra + Century (2 assets)**: `kshetra`,
> `gochara_v3_century_materialize` (lines 150–151).

This cluster maps to canonical asset IDs (underscore-prefixed per CLAUDE.md §N.1):
`ka_graha_sancara`, `ka_dasha_kala`, `ka_muhurta_seva`, `ka_gochara_resonance`, `ka_kota_chakra`,
`ka_moorti_nirnaya`, `ka_sudarshana_varsha`, `ka_tithi_pravesha`, `ka_vedha_gochara` — **9 assets,
all T0** per the elevation plan's own tiering. `ka_gochara_sweep` (protected, outside the
22-denominator) is **not** part of Frontier; it is not named in Stream A/B/C at all and per
CLAUDE.md §B it is "never rebuilt" — it belongs to no active stream. This is noted, not resolved,
in Orphan Obligations below.

**Independent corroboration found while cross-referencing F2:** `_work/F2.md`'s per-asset ancestor
closure table (lines 106–129) shows a set of exactly 12 assets that reached an ancestor
`asset_frozen` event — 9 of the 12 are precisely this Frontier cluster (`ka_dasha_kala`,
`ka_gochara_resonance`, `ka_graha_sancara`, `ka_kota_chakra`, `ka_moorti_nirnaya`,
`ka_muhurta_seva`, `ka_sudarshana_varsha`, `ka_tithi_pravesha`, `ka_vedha_gochara`), all frozen
under `t0-2026-09-01-0e5b06fb`. The other 3 of the 12 (`ka_gochara`, `ka_tulana`, `ka_yojaka`) are
Stream B/mixed. This is a second independent signal (DB campaign-event history, not the plan
document) landing on nearly the same 9-asset set the plan calls "Frontier" — treated here as
corroboration, not proof, since the plan's own stream assignment (not the DB coincidence) is the
citation basis used for scope.

---

## Per-asset rows

Column order: contribution-register disposition + DP obligations → L3 strategy A-nn row +
required transformation → L3-Q questions → product P-nn → proving journeys → U-nn → receiving
operator → F13/F14 ladder position.

### `ka_graha_sancara`

- **Contribution-register disposition + DP:** "Position/motion service." Delta: "P/I/Q: arbitrary
  instant/frame provenance; self-test is bounded service proof. DP07." (`MADHAV_DATA_PLANE_ASSET_
  CONTRIBUTION_REGISTER_v2_0.md:134`)
- **L3 strategy row + transformation:** **L3-A01** — "Ephemeris/Swiss service probe; zero
  materialized rows." Required: "Preserve numerical service and state safety. Prove exact
  conventions, time, arbitrary-chart input, provenance and failures; a canonical probe is not full
  service qualification." Wave **W2**. (`MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md:271`)
- **L3-Q questions improved:** No strategy-doc row names Q-ids for this asset directly (it is a
  compute substrate, not a synthesis writer). Inferred by content match, not an explicit citation:
  foundational to **L3-Q01** (exact structure/participants require precise positions),
  **L3-Q03** (activation route needs exact geometry), **L3-Q09** (input-sensitivity recompute
  under declared variants). Flagged as inferred, per audit rigor standard.
- **Product P-nn served:** Via the above inferred Q-links: P09–10/P22 (Q01), P09 (Q03), P13/P19
  (Q09). No direct citation — inferred chain, not stated in either source doc.
- **Proving journeys:** Foundational/indirect participant in all three (§12.1 needs "qualified
  structural relationships" computed from positions; §12.2 needs "nearest transit contact"; §12.3
  needs recompute of positions "at the time" for retrospective checking) — `MADHAV_PRODUCT_
  DEFINITION_v3_0.md:429-447`. Not named as a row-serving asset in any of the three; contributes
  only as the geometry substrate underneath assets that are named.
- **U-nn:** Not directly named in DOMAIN_F's U01–U11 table. No U-id owns `ka_graha_sancara`
  explicitly — it underlies the ephemeris compute other U-items ride on. **Gap noted below
  (Orphan obligations).**
- **Receiving operator today:** **Divergent, not the writer's own code path.**
  `_work/F5.md:19-30` (Settled divergence #1): `call_ephemeris_at_t`
  (`platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts:221-257`) calls the
  sidecar's `/api/compute/ephemeris_at_t` route (`platform/python-sidecar/routers/ephemeris.py:241`),
  which does its **own** `import swisseph as swe` (`ephemeris.py:5`) with its own
  `_AT_T_AYANAMSHA_MAP` (`:225-231`) — an in-file comment (`:211-212`) states this is deliberate,
  "rather than a second swisseph integration," i.e. it explicitly does **not** call
  `services/ka_graha_sancara/engine.py` even though that module exists and is docstring-labeled the
  "Core ephemeris-at-T engine for ka_graha_sancara" (`engine.py:2`). Confidence: high (F5's own
  grade). **The receiving operator that exists today is a parallel implementation, not
  `ka_graha_sancara`'s own registered code.**
- **F13/F14 ladder under t3 (`t3-2026-09-11-8b884eac`):**
  - F13 (asset-behavior ladder): **present** (writer/service exists, no dedicated `kala_*` table —
    `target_table = null` per F5:62 "compute service"), **not qualified** under the current
    definition (0 events, F2:112/128), **not consumed** by its own name (the live consumer calls a
    separate swisseph integration, F5:19-30) — so "consumed" only holds for the *capability*, not
    for this specific writer's code. effect-traceable/served/value-evaluated: **COULD NOT VERIFY**
    (no prior-cycle packet traced output-to-response effect for this asset).
  - F14 (campaign-event ladder): 1 ancestor definition with any event (`t0-2026-09-01`), ancestor
    `asset_frozen` = **yes** (t0), events under t3 = **0** (`F2.md:113`). Under the current t3
    definition, this asset sits at "no campaign evidence" — its only elevation evidence is
    pre-t3 and unre-verified.

### `ka_dasha_kala`

- **Contribution-register disposition + DP:** "Clock retrieval, ancestry and system traversal."
  Delta: "P/E/I/Q: precise ISO intervals, actual overlap and applicability/failed-system coverage;
  label approximate subdivisions. DP07/08." (`..._REGISTER_v2_0.md:135`)
- **L3 strategy row + transformation:** **L3-A02** — "L1 `chart_dashas` service probe across seven
  systems; zero rows." Required: "Preserve L1 clock authority. Expose actual hierarchy,
  applicability, intervals, failed/silent systems and qualified overlap; no layer-local clock
  restatement." **W2**. (`..._STRATEGY_v1_0.md:272`)
- **L3-Q questions improved:** Direct content match (not an explicit per-asset table in the
  source, but the clearest of the 9): **L3-Q01** ("which exact structure... and qualified clocks
  are engaged" — `STRATEGY:...` table row, §2), **L3-Q05** ("why do timing methods disagree" —
  directly about multi-dasha-system disagreement), **L3-Q06** ("how does this chapter differ from
  the preceding one" — clock hierarchy/recurrence). (`..._STRATEGY_v1_0.md` §2 table)
- **Product P-nn served:** Per the Q-table's own "Primary proof" column citations: P09–10/P22
  (Q01), P15/P19/P21 (Q05), P10 (Q06).
- **Proving journeys:** **Directly named as needed** in §12.1 ("ask which qualified clocks engage
  those same participants and conditions") and implied in §12.3 ("Retrieve the original completed
  reading and frozen claim" — needs the original clock window). `MADHAV_PRODUCT_DEFINITION_
  v3_0.md:433,445`.
- **U-nn:** Closest is **U02** ("Clocks→concordance... no date-equality shortcuts") — but
  `DOMAIN_F.md:24` shows `kala_dasha_sandhi_get` (the tool most plausibly serving U02) reads "L1
  `chart_dashas` via §N.5 JOIN" per its own docstring, **not** any `ka_dasha_kala`-owned table —
  consistent with, and corroborating, the F5 divergence below. So U02 is LIVE as a tool, but its
  code path does not appear to touch `ka_dasha_kala`'s own writer output either.
- **Receiving operator today:** **NOT-FOUND — real gap, per F5 (§N.8 flag, not asserted either
  way).** `_work/F5.md:32-37,66,85-86`: `call_dasha_eligibility`
  (`call_service_wrappers.ts:271-364`) runs a raw SQL query directly against L1 `chart_dashas`
  (`:346-364`); no `KaDashaKalaService` import anywhere in the file; `grep target_table|INSERT INTO`
  on `services/ka_dasha_kala/writer.py` found no hits. F5's own conclusion: "unclear whether
  `ka_dasha_kala`'s own writer output is consumed anywhere at all." **No confirmed receiving
  operator for this writer's own code today.**
- **F13/F14 ladder under t3:**
  - F13: **present** (writer exists, `writer.py:113` per F5:66), qualification/consumption status
    is the open question itself — F5 could not confirm "consumed" for the writer's own output at
    all, only for the *capability name* via a bypass path. effect-traceable/served/value-evaluated:
    **COULD NOT VERIFY**, and arguably **blocked** — if the writer's own output has no consumer,
    it cannot be effect-traceable by definition.
  - F14: ancestor `asset_frozen` = **yes** (t0-2026-09-01, `F2.md:112`), events under t3 = **0**.
    Same structural position as `ka_graha_sancara` — frozen only pre-t3, never re-verified.

### `ka_muhurta_seva`

- **Contribution-register disposition + DP:** "Calendar/action-time computation and search
  service." Delta: "P/I/Q: calendar correctness, personal suitability and outcome are distinct;
  real undertaking constraints and scope. DP07/09." (`..._REGISTER_v2_0.md:156`)
- **L3 strategy row + transformation:** **L3-A03** — "Panchanga/election service probe; zero
  rows." Required: "Test actual time/location and undertaking constraints; distinguish general
  calendar from personal feasibility and outcome expectation. Service-health proof alone is
  insufficient." **W2; real accepted-input use W7.** (`..._STRATEGY_v1_0.md:273`)
- **L3-Q questions improved:** **L3-Q10** ("Which feasible initiation intervals meet this
  undertaking's constraints? ... General calendar, personal suitability, action constraints and
  outcome expectation remain separate" — near-verbatim match to the strategy row's own language).
  Also named directly in the elevation plan's **Q7** ("'Nearest vs strongest' — by which criterion,
  for your actual use?" — `tulana, muhurta_seva, kalasutra`,
  `MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md:190`), an open native-discussion item, not yet an
  answered Q-obligation.
- **Product P-nn served:** P11/P21–22 (per L3-Q10's own citation).
- **Proving journeys:** **Not named** in any of §12.1–12.3's text. It is the direct answer to P11
  ("When might I initiate something") but none of the three worked examples (financial promise,
  NBRY, historical challenge) invoke election/muhurta. **This is a real gap** — flagged in Orphan
  Obligations.
- **U-nn:** Not directly named in DOMAIN_F's U01–U11 table (which is about clocks/vedha/kalasutra/
  Phala/claim-issuance, not election). **No U-id found covering muhurta_seva.**
- **Receiving operator today:** **LIVE, same-code, medium confidence.** `_work/F5.md:58`:
  `call_service_wrappers.ts` (`call_muhurta_score`) and `platform-mcp/src/tools/
  muhurta_finder.ts` — in-file comment states it reuses the same `score_muhurat()` primitive, not a
  reimplementation (F5's caveat: the primitive's source itself was not opened to confirm identical
  function object — medium confidence, not high).
- **F13/F14 ladder under t3:**
  - F13: **present** (service exists, `writer.py:72`/`service.py`), **consumed** (medium
    confidence — call chain verified, shared-primitive claim not independently re-derived).
    qualified/effect-traceable/served/value-evaluated: **COULD NOT VERIFY** this pass.
  - F14: ancestor `asset_frozen` = **yes** (t0-2026-09-01, `F2.md:117`), events under t3 = **0**.

### `ka_gochara_resonance`

- **Contribution-register disposition + DP:** "Event-target assembly and provenance." Delta:
  "P/I/Q/C: reconcile structural compilation with Yojaka/Kshetra, preserving unique roles rather
  than rival promise definitions. DP06/08." (`..._REGISTER_v2_0.md:136`)
- **L3 strategy row + transformation:** **L3-A05** — "`gochara_resonance_map`: chart × class ×
  target type/reference, weights and rule citations." Required: "Preserve target discovery.
  Deduplication must not retain only the first root; complete target/role/method context and
  structural binding must survive. Target contact is not automatically complete mechanism
  activation." **W2**. (`..._STRATEGY_v1_0.md:275`)
- **L3-Q questions improved:** **L3-Q07** ("Which domains interact over time? ... Qualified
  structural linkage plus coincident/ordered intervals" — matches "event-target assembly" and
  "structural compilation" language) and **L3-Q03** ("Does a named configuration have a complete
  activation route? ... active participants" — target/participant assembly is a direct input to
  activation-route determination).
- **Product P-nn served:** P01/P03–10/P17 (Q07's citation), P09 (Q03's citation).
- **Proving journeys:** **Candidate evidence source for §12.2** (NBRY) — "List eligible activation
  routes, closest contact... A participant's nearest transit contact is not automatically the
  activation of the whole configuration" (`PRODUCT_DEFINITION_v3_0.md:441`) is exactly the kind of
  target/contact data this asset assembles. Not explicitly named; inferred from content match.
- **U-nn:** Not directly named in DOMAIN_F's U01–U11 table. `register_gochara_windows.ts` (its
  consumer, see below) sits inside the DOMAIN_F "DIVERGENT carryover" note but that note is about
  the *neighboring* `ka_gochara` asset's table-name mismatch, not this asset.
- **Receiving operator today:** **LIVE, high confidence, exact table match.** `_work/F5.md:48`:
  writer does `INSERT/DELETE gochara_resonance_map` (`services/ka_gochara_resonance/writer.py:417,
  420,502`); consumer `register_gochara_windows.ts:1007` reads `FROM gochara_resonance_map` — exact
  table-name match, writer→consumer, high confidence.
- **F13/F14 ladder under t3:**
  - F13: **present**, **consumed** (high confidence — this is the cleanest receiving-operator
    match of all 9 Frontier assets). qualified/effect-traceable/served/value-evaluated:
    **COULD NOT VERIFY**.
  - F14: ancestor `asset_frozen` = **yes** (t0-2026-09-01, `F2.md:114`), events under t3 = **0**.

### `ka_kota_chakra`

- **Contribution-register disposition + DP:** "Ring/run primitives and method-specific posture."
  Delta: "P/I/Q: actual source geometry and scope; not an independent adverse vote by default.
  DP02/08." (`..._REGISTER_v2_0.md:138`)
- **L3 strategy row + transformation:** **L3-A07** — "`kala_kota_chakra`: chart × ayanamsha ×
  graha × interval start, rings/severity/roots." Required: "Preserve ring testimony, exact version
  and applicability; replace mutable latest-version selection with pinned authority. **Current v3
  implementation does not consume it: qualify and prove any proposed integration.**" **W2**.
  (`..._STRATEGY_v1_0.md:277`)
- **L3-Q questions improved:** Inferred (no explicit Q-cite): **L3-Q03** (activation route
  evidence — ring/run testimony feeds a participant-contact determination) and, per T5's tension
  analysis, this asset is explicitly named as "**not an independent adverse vote by default**"
  (register text repeated verbatim in T5's integrator table, `_work/T5.md:225` — inside
  `ka_gochara_v3_century_materialize`'s row) — i.e. its main current Q-relevance is as a
  *non-independent* witness feeding Stream C, a caveat on Q07/Q04-style domain-interaction claims
  rather than a clean contribution.
- **Product P-nn served:** No direct citation found; inferred via Q03 → P09.
- **Proving journeys:** Candidate evidence for §12.2 (ring/severity testimony as one input to
  "opposing conditions with scope and uncertainty") — not named explicitly.
- **U-nn:** **Not covered.** DOMAIN_F's U03 names "Vedha/TRIGGER/Vighnakara→integrators"
  specifically — `ka_kota_chakra` is not one of the named assets in that U-id despite being a
  structurally similar witness type. **No U-id found covering `ka_kota_chakra` at all.** Flagged
  in Orphan Obligations.
- **Receiving operator today:** **LIVE, high confidence, exact table match — but strategy doc
  flags the integration as unproven.** `_work/F5.md:54`: writer targets `kala_kota_chakra`
  (`services/ka_kota_chakra/writer.py:206`); consumer `query_kota_chakra.ts` +
  `kala_views/now.ts` reads `FROM kala_kota_chakra` directly — high confidence *as a table read*.
  But `L3-A07`'s own required transformation states "current v3 implementation does not consume
  it" — i.e. the strategy document and F5's consumer-path finding are in tension: F5 finds a live
  reader; STRAT says the century-materialize v3 pipeline specifically does not use it. These are
  not necessarily contradictory (two different downstream consumers), but neither prior-cycle
  packet reconciled them — flagged, not resolved, here.
- **F13/F14 ladder under t3:**
  - F13: **present** (585 rows, canonical chart, `_work/F7.md:53`), **consumed** at the
    `kala_views/now.ts` surface (high confidence per F5) while simultaneously **not consumed** by
    the century-materialize v3 pipeline per STRAT:277 — asset sits at different F13 rungs
    depending on which consumer is asked about. qualified/effect-traceable/served/
    value-evaluated: **COULD NOT VERIFY**.
  - F14: ancestor `asset_frozen` = **yes** (t0-2026-09-01, `F2.md:116`), events under t3 = **0**.

### `ka_moorti_nirnaya`

- **Contribution-register disposition + DP:** "Run detection and truncated-ingress safeguards."
  Delta: "P/I/Q: source-adjudicate implemented 27-nakshatra convention before broader authority.
  DP02/08." (`..._REGISTER_v2_0.md:139`)
- **L3 strategy row + transformation:** **L3-A06** — "`kala_moorti_nirnaya`: chart × ayanamsha ×
  graha × interval start, quality." Required: "Qualify the rolling −60/+400-day, day-grade Lahiri
  coverage and reference-offset handling across the horizon. Preserve method-native result; do not
  silently reuse this limited overlay as century-complete. **Actual v3 input.**" **W2**.
  (`..._STRATEGY_v1_0.md:276`)
- **L3-Q questions improved:** Inferred: **L3-Q05** (method-native context/coverage — "day-grade
  Lahiri coverage," "reference-offset handling" match Q05's "method-native context, applicability").
  Distinct from `ka_kota_chakra`: STRAT explicitly marks this one an *actual* v3 input (unlike
  kota_chakra's "does not consume it") — stronger current integration.
- **Product P-nn served:** No direct citation; inferred P15/P19/P21 via Q05.
- **Proving journeys:** Candidate evidence for §12.2 (run-detection quality feeding "closest
  contact" determination). Not named explicitly.
- **U-nn:** **Not covered** — same gap as `ka_kota_chakra`; not named in any of U01–U11.
- **Receiving operator today:** **LIVE, high confidence, exact table match, and STRAT-confirmed
  actual v3 input** (stronger than kota_chakra). `_work/F5.md:56`: writer targets
  `kala_moorti_nirnaya` (`services/ka_moorti_nirnaya/writer.py:174`); consumer
  `query_moorti_nirnaya.ts` + `kala_views/now.ts` reads `FROM kala_moorti_nirnaya` directly.
- **F13/F14 ladder under t3:**
  - F13: **present** (71 rows, canonical chart, `_work/F7.md:54`), **consumed** (high confidence,
    and the strategy doc's own text corroborates active v3 usage — the strongest F13 position of
    the 9). qualified/effect-traceable/served/value-evaluated: **COULD NOT VERIFY**.
  - F14: ancestor `asset_frozen` = **yes** (t0-2026-09-01, `F2.md:118`), events under t3 = **0**.

### `ka_sudarshana_varsha`

- **Contribution-register disposition + DP:** "Annual three-reference wheel." Delta: "P/I/Q:
  preserve actual annual scope; not static `bo_sudarshana` duplication or proof of full sub-daśā.
  DP07/08." (`..._REGISTER_v2_0.md:141`)
- **L3 strategy row + transformation:** **L3-A10** — "`kala_sudarshana_varsha`: chart × ayanamsha ×
  year, three reference-frame results." Required: "Preserve frame-specific annual testimony and
  applicability; shared natal roots are not three independent witnesses. **Current v3 does not
  read it; integration requires a qualified operator, not a dependency label.**" **W2**.
  (`..._STRATEGY_v1_0.md:280`)
- **L3-Q questions improved:** Inferred: **L3-Q05** (non-comparable scales/method-native context —
  "annual" vs natal scale) and directly implicated in elevation plan **Q3** ("What counts as an
  independent witness? Sangam currently treats shared natal roots as independent; Sudarshana's
  three frames share roots too" — `sangam, sudarshana_varsha`,
  `MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md §5`), an unresolved native-discussion item.
- **Product P-nn served:** No direct citation; inferred P15/P19/P21 via Q05.
- **Proving journeys:** Not named in §12.1–12.3. Annual-chart technique plausibly relevant to
  §12.1's "Window A/B" framing but not cited.
- **U-nn:** **Not covered** — not named in any of U01–U11.
- **Receiving operator today:** **LIVE, medium-high confidence — but STRAT explicitly says the
  live v3 pipeline does not read it.** `_work/F5.md:51`: writer targets `services/
  ka_sudarshana_varsha/writer.py:116`; consumer `query_sudarshana_varsha.ts` (a dedicated query
  file named after the asset) + `kala_views/now.ts`. Same tension pattern as `ka_kota_chakra`:
  a live consumer surface exists at the query-file level while STRAT:280 says "current v3 does not
  read it" — two different consumer claims, not reconciled by any prior packet.
- **F13/F14 ladder under t3:**
  - F13: **present** (120 rows, canonical chart, `_work/F7.md:57`), **consumed** at the query-file
    surface (medium-high) while STRAT disputes whether the *production v3 pipeline* consumes it.
    qualified/effect-traceable/served/value-evaluated: **COULD NOT VERIFY**.
  - F14: ancestor `asset_frozen` = **yes** (t0-2026-09-01, `F2.md:121`), events under t3 = **0**.

### `ka_tithi_pravesha`

- **Contribution-register disposition + DP:** "Return bracketing, annual-chart and numerical
  search kernels." Delta: "P/Q/E: named method/equation needs source adjudication; current
  Moon-longitude return is not accepted merely from name. DP02/07." (`..._REGISTER_v2_0.md:142`)
- **L3 strategy row + transformation:** **L3-A09** — "`kala_tithi_pravesha`: chart × ayanamsha ×
  year, return graha/lagna and convergence." Required: "Qualify the implemented Moon-return method
  against the admitted method before promotion. Preserve return identity and source; add an
  explicit use decision. **Current v3 does not read it.**" **W2**. (`..._STRATEGY_v1_0.md:279`)
- **L3-Q questions improved:** Inferred: **L3-Q06** ("How does this chapter differ from the
  preceding one? ... Recurrence with changes in participants, conditions" — an annual-return chart
  is structurally a yearly chapter comparison) and **L3-Q05** (method identity/adjudication).
  Directly implicated by elevation-plan **Q2** ("Three assets are consumed by nothing today —
  `ka_kota_chakra`, `ka_tithi_pravesha`, `ka_sudarshana_varsha`. Wire them into a qualified
  operator, or retire with evidenced disposition?" — `MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md §5`,
  an unresolved native-discussion item naming this exact asset among the three).
- **Product P-nn served:** No direct citation; inferred P10 (Q06), P15/19/21 (Q05).
- **Proving journeys:** Not named in §12.1–12.3.
- **U-nn:** **Not covered** — not named in any of U01–U11.
- **Receiving operator today:** **LIVE, high confidence, exact table match — but the elevation
  plan's own Q2 explicitly disputes this asset is consumed by anything today.** `_work/
  F5.md:57`: writer targets `kala_tithi_pravesha` (`services/ka_tithi_pravesha/writer.py:234`);
  consumer `query_tithi_pravesha.ts` + `kala_views/now.ts` reads `FROM kala_tithi_pravesha`
  directly (high confidence, exact table). Yet Q2 in the elevation plan groups this asset with two
  others as "consumed by nothing today" and calls "declared as a dependency... not use" — this is
  the sharpest source-tension found for any Frontier asset: the consumer-path trace (F5) says
  same-code/high-confidence table read exists; the strategy document says nothing consumes it.
  Flagged, not resolved — a genuine question for the native (already logged as elevation-plan Q2).
- **F13/F14 ladder under t3:**
  - F13: **present** (120 rows, canonical chart, `_work/F7.md:60`); "**consumed**" is directly
    disputed between F5 (yes, table-level) and the elevation plan (no, unconsumed) — reported here
    as **contested**, not resolved. qualified/effect-traceable/served/value-evaluated:
    **COULD NOT VERIFY**.
  - F14: ancestor `asset_frozen` = **yes** (t0-2026-09-01, `F2.md:120`), events under t3 = **0**.

### `ka_vedha_gochara`

- **Contribution-register disposition + DP:** "Typed obstruction and disclosed approximations."
  Delta: "P/I/Q: target-specific role and dependence; avoid duplicate attenuation. DP02/08."
  (`..._REGISTER_v2_0.md:140`)
- **L3 strategy row + transformation:** **L3-A08** — "`kala_vedha_gochara`: chart × ayanamsha ×
  obstruction kind × graha × interval, school/root data." Required: "Preserve distinct schools,
  target/role, signed inhibition and sources; declare rolling/day-grade/convention coverage. Same
  evidence must not attenuate twice through TRIGGER and Vighnakara. **Actual Sangam/v3 input.**"
  **W2**. (`..._STRATEGY_v1_0.md:278`)
- **L3-Q questions improved:** **L3-Q04** ("Why can activity coexist with strain? ... Receipt/
  creation versus retention/relief; supporting and inhibiting paths can overlap" — obstruction-vs-
  activity is exactly this asset's role) and **L3-Q03** (activation route — obstruction is one of
  the "opposing conditions" a complete route must account for).
- **Product P-nn served:** P03–04 (Q04's citation).
- **Proving journeys:** **Candidate evidence for §12.2** — "opposing conditions with scope and
  uncertainty" (`PRODUCT_DEFINITION_v3_0.md:441`) is precisely typed-obstruction testimony. Also
  plausible for §12.1's "unresolved retention constraint" framing. Not explicitly named in either;
  inferred from strong content match.
- **U-nn:** **U03** — "Vedha/TRIGGER/Vighnakara→integrators (persist obstruction target/role/
  interval/source/state)" — **Y**, directly named. `DOMAIN_F.md:52`: `ka_vedha_gochara` →
  `query_vedha_gochara.ts` (`FROM kala_vedha_gochara`, high confidence). **This is the only
  Frontier asset with a confirmed, named U-id.**
- **Receiving operator today:** **LIVE, high confidence, exact table match.** `_work/F5.md:63`:
  writer targets `kala_vedha_gochara` (`services/ka_vedha_gochara/writer.py:263`); consumers
  `query_vedha_gochara.ts`, `L0_brahmagyan/query_transit_vedha.ts`, `kala_views/now.ts` all read
  `FROM kala_vedha_gochara` directly.
- **F13/F14 ladder under t3:**
  - F13: **present** (177 rows, canonical chart, `_work/F7.md:61`), **consumed** (high confidence,
    U03 = Y), the only Frontier asset with both a named U-id and a clean receiving-operator match
    with no strategy-doc contradiction. qualified/effect-traceable/served/value-evaluated:
    **COULD NOT VERIFY** — U03's own DOMAIN_F entry does not trace beyond "registered/reachable."
  - F14: ancestor `asset_frozen` = **yes** (t0-2026-09-01, `F2.md:119`), events under t3 = **0**.

---

## Orphan obligations found in this cluster

DP/F/U/Q obligations with no asset/owner, scoped to the Frontier 9:

1. **No U-id covers 5 of the 9 Frontier assets.** `ka_graha_sancara`, `ka_muhurta_seva`,
   `ka_kota_chakra`, `ka_moorti_nirnaya`, `ka_sudarshana_varsha`, `ka_tithi_pravesha` — 6, not 5,
   on recount — appear in no row of DOMAIN_F's U01–U11 table (`_work/DOMAIN_F.md:50-60`). Only
   `ka_vedha_gochara` (U03) and `ka_dasha_kala` (U02, with the caveat that U02's actual code path
   bypasses it) have a named U-id. `ka_gochara_resonance` and `ka_muhurta_seva` likewise have no
   named U-id. This means **most of the Frontier cluster's product-facing consumer obligation is
   undocumented in the U01–U11 list** — either the U-list is incomplete for witness-tier assets
   (kota_chakra/moorti_nirnaya/sudarshana_varsha/tithi_pravesha are all "method-native testimony"
   assets of the same shape as vedha_gochara, which *does* have a U-id), or these assets genuinely
   have no stated product obligation, which would make their build cost harder to justify. This
   reads as an obligation gap in the U-list, not evidence the assets lack value — but it was not
   resolved by any prior-cycle packet and is not resolved here.
2. **`ka_muhurta_seva` has no proving-journey citation.** None of Product §§12.1–12.3 name it,
   despite it being the clean, direct answer to P11 and the subject of its own explicit L3-Q10 row.
   Product §12 only illustrates 3 of the ~24 P-ids; this may simply be sampling, not a real gap —
   flagged for completeness, not asserted as a defect.
3. **`ka_gochara_sweep`'s stream is undefined.** It is outside the 22-active denominator per
   CLAUDE.md §B and not named in Stream A/B/C at all (`MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md §4`).
   Since T1 is being split strictly along the Frontier/Spine/Kshetra+Century partition, and that
   partition never mentions the protected asset, **no cluster currently owns a T1 row for
   `ka_gochara_sweep`** unless one of the three T1 sub-agents explicitly claims it by exception.
   This agent does not claim it (it is not in Stream A "Frontier" by the plan's own text) —
   flagging so it is not silently dropped across all three T1 parts.

## Orphan work found in this cluster

Planned/existing work serving no stated obligation:

1. **`ka_kota_chakra` and `ka_moorti_nirnaya` have full, high-confidence, dedicated consumer
   surfaces** (`query_kota_chakra.ts`, `query_moorti_nirnaya.ts`, both also feeding
   `kala_views/now.ts`) **with no U-id claiming them** (see Orphan Obligation #1 above, restated
   from the work side). Real served code paths exist serving no named product obligation in the
   U01–U11 list — this is exactly the "orphan work" pattern the task asked to surface, not a guess:
   the code is confirmed live (F5, high confidence) and the obligation list (DOMAIN_F's U-table) is
   confirmed silent on them.
2. **`ka_sudarshana_varsha` and `ka_kota_chakra` each carry a live query-file-level consumer while
   the strategy document explicitly states the production v3 pipeline does not read them**
   (STRAT:277,280 "current v3 implementation does not consume it" / "current v3 does not read it").
   If the query-file consumer (`query_kota_chakra.ts`/`query_sudarshana_varsha.ts`) is real and
   reachable but the "v3" pipeline STRAT is describing is a *different*, more-authoritative
   consumer that genuinely ignores them, then the query-file work may be serving a shadow/legacy
   path rather than the asset's actual intended integration — this is orphan work in the softer
   sense of "code that runs but may not be the intended receiving contract." Not resolved here;
   flagged for the conductor to reconcile against Stream C's `ka_gochara_v3_century_materialize`
   work (Q4/STRAT:284, outside this cluster).
3. **`ka_tithi_pravesha`'s receiving operator is itself disputed** (F5 says consumed at
   high-confidence table level; elevation-plan Q2 says consumed by nothing) — if F5 is right, the
   asset's build cost is justified by live use; if Q2 is right, the `query_tithi_pravesha.ts`
   consumer file is orphan work reading a table nothing downstream actually needs. This is the one
   finding in this cluster with directly contradictory prior-cycle evidence, not merely an
   uncovered obligation — surfaced as the highest-priority reconciliation item for whoever merges
   the three T1 parts.
