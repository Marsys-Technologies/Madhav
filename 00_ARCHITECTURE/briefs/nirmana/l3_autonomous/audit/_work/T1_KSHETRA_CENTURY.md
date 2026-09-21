# T1 Traceability Matrix — Kshetra+Century Cluster

Status: read-only, cycle-3 (T1 part 3/3). Canonical chart `482012f1-710e-4a25-994a-93821f5871aa`.
Builds directly on prior-cycle inputs (F2, F3/KALA_DAG_RECONCILIATION, F5, F7, DOMAIN_F, T5) —
none of that work is redone here, only cited and composed into rows.

## Cluster definition (how determined, with citation)

The task brief's working description of this cluster ("`ka_kshetra` + century materialiser +
`ka_sangam` + `ka_kala_darshana`") **does not match the campaign's own governing execution
document.** `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md`
§4 ("The three streams") defines the actual three-way split used by this campaign:

- **Stream A — Frontier (9 assets)**: `graha_sancara`, `dasha_kala`, `muhurta_seva`,
  `gochara_resonance`, `kota_chakra`, `moorti_nirnaya`, `sudarshana_varsha`, `tithi_pravesha`,
  `vedha_gochara` (`MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md:135-136`).
- **Stream B — Spine (10 assets)**: `avadhi`, `yojaka`, `gochara`, **`sangam`**, `kalasutra`,
  `vighnakara`, `taranga`, **`kala_darshana`**, `tulana`, `bhavishya_lekha`
  (`MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md:143-144`).
- **Stream C — Kshetra + Century (2 assets, ~29k LOC)**: `kshetra`,
  `gochara_v3_century_materialize` only (`MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md:150-151`,
  `:153-154`: "Two assets, more code than the other twenty combined... Near-independent; carries
  most of the performance programme.").

**Correction applied:** per the task's own instruction ("if it differs from this description, use
the actual document's grouping and note the correction"), this report's **primary cluster is the
2-asset Stream C: `ka_kshetra` and `ka_gochara_v3_century_materialize`.** `ka_sangam` and
`ka_kala_darshana` structurally belong to Stream B (Spine), confirmed independently by the
Tier table in the same document (`ka_sangam` = T2, `ka_kala_darshana` = T4,
`MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md:100-107`) and by the L3 strategy's own asset map (STRAT
rows L3-A15 `ka_sangam`, L3-A19 `ka_kala_darshana`, both distinct rows from L3-A14 century and
L3-A22 kshetra, `MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md:284-292`).

Per the charter's own instruction ("better an asset appears in 2 clusters' reports, flagged, than
in none"), **full rows for `ka_sangam` and `ka_kala_darshana` are included below anyway**, marked
**AMBIGUOUS / CROSS-CLUSTER — STRUCTURALLY SPINE**, because: (a) the task brief explicitly named
them as the "pivotal T2/T4 tier" assets citing the critical-path chain, (b) `_work/T5.md`
(Tensions 4 and 5) already produced detailed findings on both that would otherwise sit uncited by
any of the three cluster reports if the Spine-owning subagent also treats them as out of scope by
a different boundary judgment, and (c) `ka_sangam` is the single common ancestor/chokepoint for
five of eight L3 integrators (`T5.md:227-232`) and therefore the highest-severity asset to risk
dropping from every report.

**This report's cluster, in row order below:** `ka_kshetra`, `ka_gochara_v3_century_materialize`
(primary, Stream C) — then `ka_sangam`, `ka_kala_darshana` (secondary, flagged ambiguous/Spine).

---

## Per-asset rows

### `ka_kshetra` (Stream C, primary)

| Column | Content |
|---|---|
| **Contribution-register disposition + DP obligations** | REG line 151: "Typed stages, integration/search, provenance and uncertainty/selection machinery." Obligation (P/E/I/Q): "retain engineering; preserve signed edges, complete lineage, occurrence/condition and qualified clock jurisdiction before expanding model authority." **DP06/07/08.** Evidence anchor: `S/ka_kshetra/stage2_promise.py:317–526; stage3_clocks.py:550–586` (`MADHAV_DATA_PLANE_ASSET_CONTRIBUTION_REGISTER_v2_0.md:151`). |
| **L3 strategy row (A-nn) + required transformation** | **L3-A22** `ka_kshetra` — "Chart/class continuous field plus structural routes, kinematics, clocks, primitives, nulls, windows, provenance, salience, insights and snapshots." Required: "Treat as a staged data system, not one opaque writer. Preserve its continuous-field capital; recover full signed structural semantics, immutable inputs, exact null interpretation, useful projections and event-free purpose. Apply P0/P1/P2/P6 before expensive rebuilds." Wave: **Internal W2–W7 DAG** (`STRAT:292`). Internal DAG per STRAT §6.2 (`:295-324`): 9 data families (`kala_field_kinematics`, `kala_field_promise_nodes/edges/routes`, `kala_field_clocks/boundaries`, `kala_field_primitives`, `kala_field`, `kala_field_null/windows`, `kala_field_provenance`, `kala_field_salience/kala_insights`, `kala_timeline_spec/kala_field_snapshots`) with stage order `S0 kinematics → S1 primitives; S2 structure/routes → S3 clocks/boundaries → S1; S0+S2+S3+S1 → S4 field → S5 null/windows/provenance → S6 salience → S6.5 insights → S8 timeline → complete snapshot` (`STRAT:311-316`). |
| **L3-Q questions improved** | L3-Q01 (what is active now/why), L3-Q07 (which domains interact), L3-Q08 (is no-window a real negative) — inferred from the family table's "background versus enabling interval versus contact" and "searched horizon/resolution" language (`STRAT §2` L3-Q01/Q08 rows `:62,69`) matching Kshetra's clock/boundary/null families (`STRAT:301,304`). Not an asset-specific Q-mapping in the source; STRAT does not give a direct A-nn→Q-nn table, so this is a derived correspondence — treat as medium confidence. |
| **Product P-nn served** | Via L3-Q01→P09-10/P22 and L3-Q07→P01/P03-10/P17 (`STRAT:62,68` citing those P-ids) and L3-Q08→P09/P16/P18 (`STRAT:69`). Same derived-correspondence caveat as above. |
| **Proving journey(s)** | Product §12.1 ("financial promise activate / strain end") plausibly draws on Kshetra's clock/boundary/interval data per its "qualified clocks engage those same participants" language (`MADHAV_PRODUCT_DEFINITION_v3_0.md:433`), but **no direct code citation ties Kshetra's tables into that specific journey** — flagged, not asserted. |
| **U-nn consumer interface(s)** | **L3-U01** "L2→Yojaka/Kshetra" — named explicitly for this asset: "Bind real producer fields, generations, signed routes, complete domains/roots... Hydration must use exact accepted snapshots." (`STRAT:441`). DOMAIN_F's U01 row marks it **Y** testable, citing `ka_kshetra` served via `kala_views/{ahead,priority,ritual,story}.ts` (`DOMAIN_F.md:50`). |
| **Receiving operator that exists today** | `platform-mcp/src/tools/kala_views/{ahead,priority,ritual,story}.ts` — F5 marks this "same-code (surface-level)" at **low-medium confidence**: "asset_id co-occurrence only, target table not independently verified" (`F5.md:46`). |
| **F13 ladder position (present→qualified→consumed→effect traceable→served→value evaluated)** | **present: PARTIAL.** `kala_field` holds 8,570,075 rows for the canonical chart (`F7.md` §4b, confirmed count), but `kala_field_snapshots` — the S8 "complete snapshot" terminus of Kshetra's own internal DAG — is **0 rows for the canonical chart** (1 row total, globally, belonging to a different chart, `F7.md:41,137-151`). The execution plan states this outright: "Its field snapshot has **never been built** for the canonical chart" (`MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md:62`). **qualified: NO** (signed structural semantics/immutable-input recovery not evidenced done — STRAT's own required-transformation text for L3-A22 is future tense). **consumed: UNVERIFIED** (F5 low-medium confidence, table not verified). **effect traceable: NO, actively contradicted** — "a served surface hard-codes 'field empty' (PARK-5)" (`MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md:62`; corroborated `MADHAV_DUAL_CAMPAIGN_EXECUTION_PLAN_v1_0.md:166` on `origin/codex/madhav-l3-claude-code`: "`ka_kshetra` ~8.6 M field rows with a served surface hard-coding 'field empty' (PARK-5)... partially populated with referential rot, not a clean slate"). **served: NO. value evaluated: NO.** |
| **F14/gate-matrix ladder (PLAN_REVIEWED→PRODUCER_READY→DATA_ACCEPTED→LAYER_DATA_ACCEPTED→CONSUMER_INTEGRATED→DEPLOYED_ACCEPTED→VALUE_EVALUATED)** | **PLAN_REVIEWED: YES** (L3-A22 row exists, `STRAT:292`). **PRODUCER_READY: PARTIAL** — writer/staged code exists (14,113 LOC + 4,465 own tests, `MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md:62`) but the execution plan explicitly gates rebuild on P0/P1/P2/P6 of the performance programme first, and Q4 is an open native decision ("Is `ka_kshetra`'s continuous-field model the right abstraction to preserve?" — `:190`). **DATA_ACCEPTED: NO** (snapshot absent for canonical chart). **LAYER_DATA_ACCEPTED: NO. CONSUMER_INTEGRATED: NO** (PARK-5 contradicts it directly). **DEPLOYED_ACCEPTED / VALUE_EVALUATED: NO.** Campaign-events cross-check (F2): `ka_kshetra` has 1 ancestor definition with any event (`t2`), **never reached `asset_frozen`** — sits in F2's "7 assets with ancestor evidence but never ancestor `asset_frozen`" tier (`F2.md:116,141-146`), 0 events under the CURRENT definition `t3-2026-09-11-8b884eac` (`F2.md:106-108,119`). |

### `ka_gochara_v3_century_materialize` ("the century materialiser", Stream C, primary)

| Column | Content |
|---|---|
| **Contribution-register disposition + DP obligations** | REG line 140: "Numerical refinement, resumability and wide-horizon coverage." Obligation (P/Q/H): "existing hold remains; **eager century-wide work is not itself required user value.** No rematerialization here." **DP07/16.** Evidence anchor: `W/ka_gochara_v3_century_materialize.py` (`MADHAV_DATA_PLANE_ASSET_CONTRIBUTION_REGISTER_v2_0.md:140`). |
| **L3 strategy row (A-nn) + required transformation** | **L3-A14** `ka_gochara_v3_century_materialize` — "Century staging and production windows: chart × class × era × resolution × window/milestone, hierarchical parent IDs." Required: "Retain its protected hold until authority/method decisions. Redesign common preparation, target event searches and batched hierarchy writes; ensure complete overlay coverage, content-bound resume and coherent publication. Moorti/Vedha are actual inputs; Kota/Tithi/Sudarshana integration is not implemented." Wave: **W3, after its specific hold is resolved** (`STRAT:284`). |
| **Named unresolved decision (T5/execution-plan)** | `T5.md` Tension 2: REG:140's "no rematerialization" instruction and STRAT:230-234's "deferral alone cannot earn full asset elevation" are in direct tension for this exact asset — a closed loop the register does not name STRAT's own escape branch ("a qualified compact substrate with explicit refinement semantics") for (`T5.md:66-96`). Execution plan names this **Q1**: "Full century materialisation, or a qualified compact substrate with explicit refinement semantics?" — "The hold cannot close by deferral, and the answer changes ~11k LOC of work" (`MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md:187`). `T5.md` Tension 8 additionally finds the SEED's declared 6-edge `depends_on` set (including `ka_kota_chakra`, `ka_tithi_pravesha`) contradicts STRAT:284's own "Kota/Tithi/Sudarshana integration is not implemented" in the same document — two of six declared inputs are aspirational (`T5.md:271-289`). |
| **L3-Q questions improved** | No direct A-nn→Q-nn table exists in STRAT. Derived: L3-Q02 (closest eligible window / robust across variants) and L3-Q08 (is no-window a real negative, re: searched horizon/resolution) plausibly match "wide-horizon coverage" (REG:140) and "era/resolution/window" framing (L3-A14) — medium-low confidence, not source-stated. |
| **Product P-nn served** | Via the same derived L3-Q02→P03-04/P09 and L3-Q08→P09/P16/P18 correspondence (`STRAT:63,69`). Same caveat as above. |
| **Proving journey(s)** | **COULD NOT VERIFY** a direct citation tying the century materialiser into any of Product §12.1-12.3's three named journeys within budget; none of the three journey sketches mentions century-scale gochara coverage explicitly. |
| **U-nn consumer interface(s)** | **None of L3-U01–U11 names this asset explicitly** (`STRAT:441-451` reviewed in full — U03 "Vedha/TRIGGER/Vighnakara→integrators" is the nearest topical neighbor but is scoped to obstruction integrators, not the century writer). This is itself a finding — see Orphan obligations below. |
| **Receiving operator that exists today** | `platform-mcp/src/tools/retrieval/register_gochara_windows.ts` — F5 marks this "same-code" at **high confidence**: "comment block explicitly names it authoritative writer for the shared `kala_gochara_windows` table (`:576,588`)" (`F5.md:60`). Caveat: `T5.md` Tension 1 independently shows this same table name is claimed by **three** different governing surfaces for **two different assets** (`ka_gochara` per STRAT/writer/migration-1018 vs the century materialiser per SEED, `T5.md:18-62`) — the "authoritative writer" claim sits inside an unresolved 5-way table-identity dispute. |
| **F13 ladder position** | **present: PARTIAL.** `kala_gochara_windows_v2` holds 1,001 rows for the canonical chart, split `g3_utkarsha`→914, `2.0`→87 (`F7.md:50,96`); the `g3_utkarsha`-tagged rows are the century materialiser's own era-slice output per its SEED description ("DELETE-then-INSERTs into `kala_gochara_windows_v2` with `era_slice_key=g3_{year_start}_{year_end}`", `T5.md:40-41`). So real prior-generation data exists, but under an active hold that the register says should not be extended ("No rematerialization here"). **qualified: NO** (hold unresolved; Q1 open). **consumed: PARTIAL** (F5 high-confidence writer→consumer table match, but see the table-identity caveat above — the consumer may not be reading exactly this asset's rows uniquely). **effect traceable / served / value evaluated: NOT EVIDENCED** — no U-nn packet and no proving-journey citation found this pass. |
| **F14/gate-matrix ladder** | **PLAN_REVIEWED: YES** (L3-A14, REG:140, both exist). **PRODUCER_READY: PARTIAL** — 2,480 writer LOC + `gochara_v3` 8,441 LOC exist (`MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md:63`), but the writer's own declared input set overstates what it integrates (Tension 8) — a producer-readiness check run today "would report readiness it does not have" (`T5.md:284-286`). **DATA_ACCEPTED: NO** (explicitly held; STRAT:233 "deferral alone cannot earn full asset elevation" implies the current held state does not qualify). **LAYER_DATA_ACCEPTED: NO** (STRAT:396's own LAYER_DATA_ACCEPTED definition: "A held or unqualified required active capability prevents full-layer acceptance" — this asset is exactly that holdout). **CONSUMER_INTEGRATED/DEPLOYED_ACCEPTED/VALUE_EVALUATED: NO.** Campaign-events cross-check (F2): **entity-identity concern** — F2's per-asset table lists an entity `ka_gochara_v` (not `ka_gochara_v3_century_materialize` in full) with **0 ancestor defs, 0 events, ever** — one of "3 assets with zero campaign evidence in any generation" that "expanded the roster from the original 12 to the current 22" (`F2.md:113,147-150`). **COULD NOT VERIFY** within this pass's budget whether `ka_gochara_v` is a truncated/aliased entity_id for this asset or a genuinely distinct, unrelated identity string in the events table — if it is this asset under a mismatched entity_id, then the campaign's own evidence-tracking mechanism cannot currently attach any event to it at all, which is a second, independent reason (beyond the Q1 hold) that no F14 rung above PLAN_REVIEWED can be honestly claimed. Flagged for the conductor to resolve with a direct query. |

---

### `ka_sangam` — AMBIGUOUS / CROSS-CLUSTER — STRUCTURALLY SPINE (T2 tier, `MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md:104`)

| Column | Content |
|---|---|
| **Contribution-register disposition + DP obligations** | REG:148: "Targeted/exploratory convergence and contact search." Obligation (P/E/I/Q): "consume full configuration/domains/conditions, not first domain or missing-dignity 0.5." **DP06/08.** Evidence: `W/ka_sangam.py:331–377` — spot-verified **clean** by `T5.md` Tension 9 (anchor holds at `:333,348,352-353,360,362`). |
| **L3 strategy row (A-nn) + required transformation** | **L3-A15** — `kala_convergence`: chart/signal/mode/window, score/orb/rarity/constituents; "one domain and missing ayanamsha identity need review." Required: "Preserve useful modes and live transit search. Share only compatible geometry; retain complete predicates, routes, context, real simultaneous testimony and all evidence roots. Remove hidden coverage caps and default independent-witness claims." Wave: **W3** (`STRAT:285`). |
| **Named unresolved decision** | `T5.md` Tension 4 (REG:148's "not first domain or missing-dignity 0.5" is unmet, both patterns verbatim present and *unannotated* in code, contrast century's analogous defect which *was* annotated — `T5.md:144-172`); Tension 6 (de-correlation detector `engine.py:850-889` scoped to vocabulary not asset provenance, is common ancestor of 5/8 integrators — `T5.md:210-232`); Tension 7 (declared `ka_gochara` dependency resolves to a namesake service with no table, not the registered writer's output — `T5.md:238-269`). Execution plan calls it **"the chokepoint — 7 of 21 depend on it"** (`MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md:64`) and flags **Q3** ("what counts as an independent witness?") against it (`:189`). |
| **L3-Q questions improved** | L3-Q02 (closest/best-supported window, "Controlled ranking on matched candidates and coverage" — `STRAT:63`), L3-Q07 (domain interaction/structural bridge — `:68`) — plausible match to convergence/mode/window shape; not source-stated as an explicit mapping. |
| **Product P-nn served** | Via L3-Q02→P03-04/P09 and L3-Q07→P01/P03-10/P17. |
| **Proving journey(s)** | Product §12.1 ("financial promise activate / strain end... which qualified clocks engage those same participants") and §12.2 (NBRY activation, "closest contact, better-supported windows") both plausibly depend on convergence-window data of exactly ka_sangam's shape; no direct code citation confirms this journey reads `kala_convergence` specifically. |
| **U-nn consumer interface(s)** | No `ka_sangam`-specific U-id, but it underlies **U02** (Clocks→concordance) and **U04** (Kalasutra/Tulana→AHEAD/NOW) by dependency (`ka_kalasutra`, `ka_taranga`, `ka_vighnakara`, `ka_kala_darshana` all consume it, `T5.md:218-225`). DOMAIN_F marks U02 "Y (tool exists), logic depth COULD NOT VERIFY" and U04 "Y, with a known gap" (`DOMAIN_F.md:51,53`). |
| **Receiving operator that exists today** | `.../L3_kala/query_convergence_windows.ts`; `query_temporal_activation.ts`; `kala_views/ahead.ts` — F5 marks "same-code" **medium confidence** (`F5.md:55`). |
| **F13 ladder position** | **present: NO for the canonical chart.** `F7.md:25`: "`kala_convergence` \| 0 \| — \| — \| Globally non-empty (20,497 rows across 2 other charts)." Zero rows exist for `482012f1-…` despite being the campaign's stated chokepoint asset. Every downstream rung (qualified/consumed/effect traceable/served/value evaluated) is **NO by construction** — there is nothing to consume for this chart. |
| **F14/gate-matrix ladder** | **PLAN_REVIEWED: YES. PRODUCER_READY: PARTIAL** (2,978 LOC exists, but REG:148 defects unresolved). **DATA_ACCEPTED: NO** (0 canonical-chart rows). **LAYER_DATA_ACCEPTED: NO** — and per KALA_DAG_RECONCILIATION §4, `ka_sangam` "has never been dispatched through a run whose manifest survived, despite 522 build_runs existing for the canonical chart... **the campaign's own freeze-and-verify mechanism is unproven for its most important asset**" (`KALA_DAG_RECONCILIATION_v1_0.md:56-60,98`). **CONSUMER_INTEGRATED/DEPLOYED_ACCEPTED/VALUE_EVALUATED: NO.** Campaign-events (F2): 1 ancestor def (`t2`), never `asset_frozen`, 0 events under `t3` (`F2.md:122`). |

### `ka_kala_darshana` — AMBIGUOUS / CROSS-CLUSTER — STRUCTURALLY SPINE (T4 tier, `MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md:106`)

| Column | Content |
|---|---|
| **Contribution-register disposition + DP obligations** | REG:155: "Convergence/obstruction presentation join." Obligation (P/I/Q/C): "qualify independent net-score authority; global top-750 and NULL→0.5 are not complete personalized search." **DP08/10/12.** Evidence: `W/ka_kala_darshana.py:21–33,85–102` — spot-verified **clean** by `T5.md` Tension 9 (`LIMIT 750` at `:31`, NULL→0.5 block at `~:82-95`). |
| **L3 strategy row (A-nn) + required transformation** | **L3-A19** — `kala_darshana`: chart/convergence/signal/window, effective score and obstruction summary. Required: "Preserve the zero-handling repair; resolve top-750 truncation and missing-convergence 0.5 default. Expose complete qualified route and coverage. Current computation reads convergence/obstruction, not `kala_activation`; a new recurrence integration must be explicit." Wave: **W5** (`STRAT:289`). |
| **Named unresolved decision** | `T5.md` Tension 5: **real split** between the two register-named defects — the NULL→0.5 half is now annotated/warned-and-documented (never-firing per code comment), but the **top-750 global cut is unchanged and unqualified**, and is the one with a *live* effect on every served row (`:186-203`). Tension 6 notes it composes `ka_sangam` × `ka_vighnakara`, and `ka_vighnakara` itself reads `ka_sangam` — "not two independent readings; both legs descend from `ka_sangam`" (`T5.md:219`). |
| **L3-Q questions improved** | L3-Q06 ("how does this chapter differ from the preceding one" — recurrence with changes) plausibly matches its "effective score and obstruction summary" join shape; not source-stated. |
| **Product P-nn served** | Via L3-Q06→P10 (`STRAT:67`). |
| **Proving journey(s)** | Product §12.2 (NBRY trigger — "list eligible activation routes, closest contact, better-supported windows and opposing conditions") is the closest topical match to a convergence×obstruction join; no direct code citation confirms it. |
| **U-nn consumer interface(s)** | No dedicated U-id; feeds `ka_bhavishya_lekha` and `ka_jivana_parva` downstream (`T5.md:221-222`), which are themselves outside this report's cluster (Spine, T5 tier). |
| **Receiving operator that exists today** | `.../L3_kala/query_temporal_view.ts` — F5 marks "same-code" **medium confidence** (`F5.md:50`). |
| **F13 ladder position** | **present: NO for the canonical chart.** `F7.md:27`: "`kala_darshana` \| 0 \| — \| — \| Globally non-empty (750 rows), all owned by chart `1c826d5a-…`." Zero rows for `482012f1-…`. This is a direct downstream consequence of `ka_sangam`'s own zero-row state for this chart (§28 dependency: `kala_convergence` (`ka_sangam`) ⋈ obstructions (`ka_vighnakara`), `T5.md:219`) — the input it would join is itself empty for this chart. All downstream F13 rungs: **NO**. |
| **F14/gate-matrix ladder** | **PLAN_REVIEWED: YES. PRODUCER_READY: PARTIAL** (234 LOC, top-750 unresolved). **DATA_ACCEPTED: NO** (0 canonical-chart rows). **LAYER_DATA_ACCEPTED: NO. CONSUMER_INTEGRATED/DEPLOYED_ACCEPTED/VALUE_EVALUATED: NO.** Campaign-events (F2): 1 ancestor def (`t2`), never `asset_frozen`, 0 events under `t3` (`F2.md:116`). |

---

## Orphan obligations found in this cluster

1. **No U-nn interface packet names the century materialiser.** All 11 of L3-U01–U11 were read in
   full (`STRAT:441-451`); none addresses `ka_gochara_v3_century_materialize` specifically, and the
   nearest topical neighbor (U03, obstruction integrators) is scoped to a different asset family.
   REG:140 and STRAT §6.1 L3-A14 both impose real obligations (resumability, wide-horizon coverage,
   the Q1 hold-resolution decision) with no receiving-operator interface packet currently assigned
   to carry them to a consumer. This is an obligation with no packet/owner — the definition of an
   orphan obligation per this task's own framing.

2. **`ka_kshetra`'s U01 obligation exists in name but has no verified satisfying receiving
   operator.** L3-U01 requires "Bind real producer fields, generations, signed routes... Hydration
   must use exact accepted snapshots" (`STRAT:441`). The only candidate receiving operator
   (`kala_views/{ahead,priority,ritual,story}.ts`) is confirmed only at "asset_id co-occurrence"
   level (F5, low-medium confidence) and is directly contradicted by PARK-5's "served surface
   hard-codes 'field empty'" finding. An obligation with a named U-id but no operator that can be
   shown to satisfy it is functionally orphaned.

3. **`ka_sangam`'s frozen-manifest protection has never been exercised for this asset despite it
   being the campaign's own named chokepoint.** KALA_DAG_RECONCILIATION §4: 12 of 23 identities
   have never been captured by a surviving `plan_manifest` snapshot, "**including `ka_sangam`, 'THE
   VALUABLE CORE'**" (`KALA_DAG_RECONCILIATION_v1_0.md:56`). The freeze-and-verify safety mechanism
   is a stated obligation of the campaign's own integrity model; it is unproven for the one asset
   the execution plan itself calls the chokepoint. Whether this is properly "this cluster's" orphan
   obligation or Spine's is exactly the ambiguity this report was asked to flag rather than drop.

## Orphan work found in this cluster

1. **`ka_kshetra`'s ~8.6M rows of built field data serve no currently-verified consumer.**
   `kala_field` (8,570,075 rows), `kala_field_provenance` (959,032), `kala_field_boundaries`
   (261,998), `kala_field_primitives` (165,082), and five more populated `kala_field_*` tables all
   hold real canonical-chart data (`F7.md` §1), representing 14,113 LOC + 4,465 tests
   (`MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md:62`) — yet "no served surface currently reads" this
   field per the execution plan's own Q4 (`:190`), and the one surface that does reference it
   hard-codes an empty result (PARK-5). This is substantial completed work serving no demonstrated
   obligation today — the canonical orphan-work case in this cluster.

2. **`ka_kshetra`'s Stage 8 six-view grain is now-orphaned work relative to the current documented
   design direction.** `T5.md` Tension 3: the value-architecture doc and the product definition
   both now state the six-view split "is not a target constraint" and should be projections, not a
   schema-enforced natural key (`VAL:218`, `MADHAV_PRODUCT_DEFINITION_v3_0.md:336`) — but
   `stage8_spec.py:53-54`'s `VIEWS` tuple and `kala_timeline_spec`'s natural key still hard-freeze
   exactly six views as a DB-enforced grain (`T5.md:99-140`). The engineering that built this grain
   ("genuinely independent work" per view, `writer.py:85`) now serves a screen-boundary rationale
   the governing docs explicitly decline to endorse.

3. **The century materialiser's declared 6-input dependency set includes 2 aspirational edges.**
   SEED declares `depends_on` including `ka_kota_chakra` and `ka_tithi_pravesha` as "full depends_on
   set reflecting the v3 writer's true runtime inputs" (`T5.md:273-278`), but STRAT:284 states in
   the same governing document that "Kota/Tithi/Sudarshana integration is not implemented." Any
   registry/DAG-completeness tooling that trusts the declared edge set reports integration work that
   does not exist — the inverse defect of orphan work (declared-but-absent work), flagged here
   because it sits inside this cluster's own asset and directly undermines any readiness signal
   drawn from the SEED for it.

---

**Method note:** stayed within the 45-tool-call budget (used well under half); nothing here
required a live DB query beyond what F7/F2 had already produced, so no new `psql` calls were made
this pass. Two items above are explicitly marked COULD NOT VERIFY per the task's own instruction
rather than guessed a third time: the `ka_gochara_v` vs `ka_gochara_v3_century_materialize`
entity_id correspondence in campaign events, and the century materialiser's proving-journey
participation.
