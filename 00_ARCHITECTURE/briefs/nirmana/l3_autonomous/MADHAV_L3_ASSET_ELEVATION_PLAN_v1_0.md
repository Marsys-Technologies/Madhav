---
artifact: MADHAV_L3_ASSET_ELEVATION_PLAN
version: "1.0"
status: DRAFT_FOR_NATIVE_REVIEW
prepared_on: 2026-09-20
prepared_by: "Strategy session (Claude Code) — structural analysis measured from source; not yet reconciled against the frozen manifest"
purpose: >
  What "elevation" concretely does to an L3 asset, which assets need the most transformation,
  and how the residual 21 split into three parallel streams. Written to be reviewed and added
  to by the native before fan-out.
pending_measurements:
  - "egate.sql L3 output — reconciles the frozen manifest against seed and live registry; may move assets between tiers"
  - "pathfinder cost — real per-asset elapsed time from ka_graha_sancara end-to-end; all sizing here is structural, not temporal"
authority: MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md (DP-SD-017) · MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md · DP-SD-021
---

# L3 Kāla — asset elevation plan

## 1. What "elevation" actually does to an asset

Elevation is **not** "make the writer work" or "produce more rows". Every one of the 22 assets
already computes something; several serve real data today. Elevation moves an asset from
*computes something* to *terminally accepted*, across ten dimensions. An asset is elevated when
all ten hold — and `Accepted N/22` counts only that.

| # | Dimension | What it demands | Source |
|---|---|---|---|
| **D1** | **Field/producer contract** | Every material field names its actual producer column/path, data type, unit, cardinality, natural key, null semantics, context, qualification, transformation, persistence, **receiving operator** and **falsifying test**. Each gap classified: missing, computed-but-discarded, persisted-but-unused, flattened, unqualified, stale, unserved. *A fetched or cited field with no declared effect has not met the use contract.* | Strategy §3 |
| **D2** | **Structure preservation** | Participants and roles, sign/polarity, all applicable domains, occurrence vs condition, cancellation, rivals, applicability, source/method, canonical L1 fact references. No scalar grade substituting for a mechanism. | Strategy §3, DP-01 |
| **D3** | **Temporal contract** | Exact intervals, inclusivity convention, overlaps, ordering, recurrence, horizons, method disagreement, uncertainty, chart/convention sensitivity, and **search completeness** (searched horizon, resolution, exclusions, failed/unsearched regions). | Strategy §3 |
| **D4** | **Upstream binding** | Reads bind to an **accepted immutable generation vector**, not mutable `public` rows. Seven L2 producers share MSR; `bo_bimba`/`bo_karanajala` share CGM nodes — one "latest head" is not the dependency vector. | Strategy §4, §6.3 |
| **D5** | **Numerical correctness** | Independently specified reference calculation, not old-output parity. Where the current method has a defect, the old output is **not** the oracle. | Strategy §5 |
| **D6** | **Cost, without semantic loss** | Measured on representative cases, same input vector/conventions/horizon/hardware/cache regime. Reduced caps, coarser resolution, fewer simulations or a narrowed horizon are **not** equivalent speedups. | Strategy §5, P0–P6 |
| **D7** | **History safety** | Publication/replay/rollback; issued claims, outcomes and referrers preserved; no collateral shared-owner mutation. A rebuild must not rewrite what the system originally said. | Strategy §4, DP-08 |
| **D8** | **Consumer integration** | An authorized receiving operator actually uses the data and a material field **changes the answer**, surviving retrieval, budgeting, delivery and replay. | U01–U11 |
| **D9** | **Deployment** | Exact protected source, migration and deployed revision, verified by actual ready revision + env SHA — not workflow colour. | Strategy §7 |
| **D10** | **Value evaluation** | The distinction is tested through the receiving operator against a competent simpler baseline. Presence, retrieval and operational success are insufficient. | Strategy §7 |

**Explicitly excluded:** empirical predictive performance. That is a separate programme and is
neither required nor claimed by this campaign.

Three recurring defect classes that elevation exists to remove, visible across many assets:

- **Silent truncation** — `top-500` (Vighnakara), `top-750` (Darshana), `default-eight`
  (Kalasutra), `LIMIT 1` unordered (Jivana Parva), `ten-row` (Avadhi), hidden caps (Sangam).
  A cap that cannot be distinguished from a true absence destroys D3's coverage contract.
- **Flattening** — multi-domain → one domain, signed → unsigned, mechanism → scalar grade,
  class-specific → domain maxima. Destroys D2.
- **Invented neutrality** — `0.5` on missing convergence (Darshana), rank-as-identity
  (Bhavishya). A favourable-sounding default standing in for "I don't know" (§N.7 item 6).

---

## 2. Which assets need significant transformation

Ranked by measured code mass, dependency position, and the severity of what §6.1 requires.

### Tier S — the three hard ones (~29k LOC, all the architectural risk)

| Asset | Mass | Why it is hard |
|---|---|---|
| **`ka_kshetra`** | **14,113 LOC** + 4,465 own tests; 15-table internal S0→S8 DAG; 13 `bo_` ancestors; ~8.6M rows already written | Not one writer — a staged data system. Continuous-field model with kinematics, routes, clocks, primitives, nulls, windows, provenance, salience, insights, snapshots. Carries **P0, P1, P2 and P6** of the performance programme. Its field snapshot has **never been built** for the canonical chart, while a served surface hard-codes "field empty" (PARK-5). Needs full signed structural semantics recovered, exact null interpretation, immutable inputs, resumability, and a complete compatible publication. |
| **`ka_gochara_v3_century_materialize`** | 2,480 writer + `gochara_v3` **8,441** | **On hold, and the hold is a real unresolved decision** (§5). Must choose between an elevated complete century materialisation and a qualified compact substrate with explicit refinement semantics. Kota/Tithi/Sudarshana are *declared* inputs its code does not consume. Deferral alone cannot earn elevation — the hold must legitimately close either way. |
| **`ka_sangam`** | 2,978 LOC | **The chokepoint — 7 of 21 depend on it.** Hidden coverage caps; default independent-witness claims from shared roots; registry declares a materialised-Gochara edge its code does not read; one-domain and missing-ayanamsha identity both need review. Shared geometry (P4) must be reused without losing per-rule/parent/method testimony. |

### Tier A — substantial semantic repair

| Asset | Mass | Core transformation |
|---|---|---|
| `ka_yojaka` | 1,304 | Compile **complete** accepted L2 mechanisms, participants, signed multi-domain relations, cancellation, all linked roots. Remove one-domain/five-link flattening with explicit migration. **79 unmatched MSR references** must resolve. Feeds 4 downstream assets. |
| `ka_vighnakara` | 864 | Opposition preserved separately from activity; resolve top-500 coverage, null-convergence association, deterministic ties, duplicated roots. *Absence of evaluation must never read as clear passage.* |
| `ka_bhavishya_lekha` | 594 | Replace unstable **rank-as-identity**; fix the empty-input deletion path first; declare five-year/top-100 scope; preserve issued claims, outcomes and referrers. **Rebuildable projections cannot own or rewrite issued history.** |
| `ka_taranga` | 257 + `taranga_kernel` 500 | Class-dasha degenerates to shared domain behaviour; class-transit to domain maxima. Use actual Pratijna/convergence/clocks/ontology; the declared Avadhi dependency is **not read** today. |
| `ka_kalasutra` | 285 | Retain all qualified recurrences and multiple convergence contributions; remove default-eight truncation and implicit "today"; explicit as-of/horizon. |
| `ka_kala_darshana` | 234 | Resolve top-750 truncation and the **0.5 default on missing convergence**; preserve real zero; expose complete qualified route and coverage. Reads convergence/obstruction, *not* `kala_activation` as the registry claims. |
| `ka_jivana_parva` | 444 | Replace **unordered `LIMIT 1`** predicate selection with a qualified relation; retain exact interval/clock/context and mechanism links; distinguish prior/later chapter changes. |

### Tier B — moderate

`ka_avadhi` (332; ayanamsha missing from key, fixed domains, ten-row limits, soft-empty),
`ka_gochara` (684; bounded ±3y coverage made explicit, content-complete geometry keys),
`ka_gochara_resonance` (599; dedup must not keep only the first root),
`ka_vedha_gochara` (908; distinct schools, signed inhibition, **no double attenuation** through TRIGGER and Vighnakara).

### Tier C — light or service-shaped

`ka_graha_sancara` (736), `ka_dasha_kala` (952), `ka_muhurta_seva` (576), `ka_tulana` (608),
`ka_kota_chakra` (535), `ka_moorti_nirnaya` (493), `ka_tithi_pravesha` (555),
`ka_sudarshana_varsha` (355).

Small code, but **four are service/pure identities** whose acceptance is service proof, not a row
build — and three of them are currently **consumed by nothing** (see §5).

---

## 3. Measured structure

**Dependency tiers** (live-registry edges; the frozen manifest may differ — see §6):

| Tier | Assets |
|---|---|
| T0 (11) | avadhi, dasha_kala, gochara_resonance, graha_sancara, kota_chakra, moorti_nirnaya, muhurta_seva, sudarshana_varsha, tithi_pravesha, vedha_gochara, yojaka |
| T1 (3) | gochara, century, kshetra |
| T2 (1) | **sangam** |
| T3 (3) | kalasutra, taranga, vighnakara |
| T4 (1) | kala_darshana |
| T5 (3) | bhavishya_lekha, jivana_parva, tulana |

Critical path six deep. **Fan-out:** sangam→7, yojaka→4, kala_darshana→3, vighnakara→3,
gochara_resonance→3, dasha_kala→3.

**L2 dependency — a clean 11/11 split.** Eleven assets carry zero `bo_*` ancestors; eleven carry
10–13. **`bo_samvada` — the one L2 asset on record as unfrozen — appears in no L3 closure**, so it
blocks nothing here.

**Shared hubs** (editing one invalidates every dependent's accepted analysis, because writer
digests cover the import closure):

| Hub | Imported by |
|---|---|
| `pipeline/transit_search.py` | kshetra, sangam, gochara family, **and L0 `bg_sky_calendar` (frozen)** |
| `services/ka_dasha_kala` | avadhi, sangam, **and L4 `ph_nimitta`** |
| `services/ka_temporal` | century, kalasutra, vighnakara, yojaka |
| `services/ka_graha_sancara` | kota_chakra, moorti_nirnaya, sudarshana_varsha, vedha_gochara |
| `gochara_grammar` / `gochara_intensity` | resonance, v3, w2g |
| `services/kala_trigger` | sangam |

---

## 4. The three streams

Assigned so each hub and its dependents sit in one stream.

### Stream A — Frontier (9 assets)
`graha_sancara`, `dasha_kala`, `muhurta_seva`, `gochara_resonance`, `kota_chakra`,
`moorti_nirnaya`, `sudarshana_varsha`, `tithi_pravesha`, `vedha_gochara`

All T0. Owns hubs `ka_graha_sancara`, `ka_dasha_kala`, `ka_muhurta_seva`,
`ka_gochara_resonance`, `gochara_grammar`, `gochara_intensity`.
**Upstream of both other streams — must run first and fastest.** This is where `N/22` moves early.

### Stream B — Spine (10 assets)
`avadhi`, `yojaka`, `gochara`, `sangam`, `kalasutra`, `vighnakara`, `taranga`, `kala_darshana`,
`tulana`, `bhavishya_lekha`, `jivana_parva`

The whole critical path. Owns `ka_temporal`, `kala_trigger`, `taranga_kernel`.
Deep and serial in its **build** order — but all D1/D2 analysis work is ungated and can proceed
in parallel while waiting on upstream freezes.

### Stream C — Kshetra + Century (2 assets, ~29k LOC)
`kshetra`, `gochara_v3_century_materialize`

Two assets, more code than the other twenty combined. Owns `services/ka_kshetra`,
`services/gochara_v3`, `w2g`. Near-independent; carries most of the performance programme.

### Why this is safe to parallelise

The E-gate has three conditions. **C2.2 — `asset_analysis_accepted` + `optimization_verdict_accepted`
— is never gated** (`egate.sql`: *"Neither is ever gated (C2), so this is always work you can do
right now"*). That is the D1/D2 contract work, available on all 21 today, in parallel.
Only the **build → verify → freeze** tail is serial.

### What stays serial regardless

1. **Physical builds** — per-chart `pg_try_advisory_lock`, one chart. One build lane, whatever the stream count.
2. **Merges** — merge queue.
3. **The L3 layer pin** — `layers.L3.writer_inventory_sha256` is one hash over all 22 writers; every L3 source PR shifts it. One integrator re-pins.
4. **Generated artifacts** — 28 of 40 recent commits touch `src/generated/`. Resolve by regenerating, never hand-editing. (Observed live three times today.)

### Rules

- **Freeze hubs before dependents.** One owner per hub, named.
- **Never change `layers.L3.convergence_commit`.** Re-pin the aggregate only, verifying only intended digests moved.
- **Never edit `transit_search.py` or `services/ka_dasha_kala` in-stream** — both sit inside already-frozen L0/L4 digest closures. Any change is a coordinated cross-stream invalidation with a named owner. Note this collides directly with performance items **P3/P4**.
- Migration range **1070–1119**; 1070 consumed.
- Sessions open PRs into an integration branch; one integrator merges to main.
- Sessions request builds from the lane; they never dispatch themselves.

---

## 5. Assets needing focused native discussion

These are **product and method judgements, not engineering**. Each needs a ruling before its asset can close.

| # | Question | Asset(s) | Why it is yours |
|---|---|---|---|
| **Q1** | **Full century materialisation, or a qualified compact substrate with explicit refinement semantics?** | century | An explicit unresolved architecture/cost decision in the strategy. The hold cannot close by deferral, and the answer changes ~11k LOC of work. |
| **Q2** | **Three assets are consumed by nothing today** — `ka_kota_chakra`, `ka_tithi_pravesha`, `ka_sudarshana_varsha`. Wire them into a qualified operator, or retire with evidenced disposition? | those 3 | Elevating an unconsumed asset means *creating* a new integration and its justification. "Declared as a dependency" is not use. A portfolio call. |
| **Q3** | **What counts as an independent witness?** Sangam currently treats shared natal roots as independent; Sudarshana's three frames share roots too. | sangam, sudarshana_varsha | Epistemics, not code. It determines whether convergence strength means anything. |
| **Q4** | **Is `ka_kshetra`'s continuous-field model the right abstraction to preserve?** It is 14k LOC and 8.6M rows that no served surface currently reads (PARK-5). | kshetra | The single largest investment in the layer. Worth confirming before P1's exact-null programme is paid for. |
| **Q5** | **Prospective claims: what may Bhavishya assert?** Rank-as-identity, five-year/top-100 scope, non-probability meaning, and the firewall between issued history and rebuildable projection. | bhavishya_lekha | Touches the Ethical Framework directly — calibrated, disclosed, non-fortune-telling output. |
| **Q6** | **Is monthly resolution over 1950–2100 the right Taranga contract**, and what should class-specific meaning be when it currently degenerates to domain maxima? | taranga | Scope and semantics, not implementation. |
| **Q7** | **"Nearest vs strongest" — by which criterion, for your actual use?** | tulana, muhurta_seva, kalasutra | L3-Q02 is a product question. The ranking kernel is fine; the criterion is a judgement. |
| **Q8** | **What is the honest truncation policy?** Every cap (top-500/750, default-eight, ten-row, `LIMIT 1`) must become either complete coverage or an explicit, reported bound. | vighnakara, darshana, kalasutra, avadhi, jivana_parva, sangam | A cross-asset policy decision; cheaper to rule once than seven times. |

---

## 6. What is not yet measured

Stated plainly so this plan is not mistaken for more than it is.

1. **The frozen manifest has not been read.** Seed and live registry **disagree on four assets** — `ka_sangam` (0 vs 10 deps), `ka_kalasutra` (0 vs 3), `ka_muhurta_seva` (1 vs 0), `ka_vighnakara` (4 vs 5). The E-gate resolves against the frozen manifest, a **third** source. §3's tiers use live-registry edges and **may move**.
2. **No per-asset cost exists.** Nobody has carried an asset through this path under `t3`. Every sizing here is structural. The pathfinder produces the first real number.
3. **Freeze state of `bg_*`/`ga_*`/`bo_*` ancestors is unread** — `egate` answers it.
4. **`ka_kshetra`'s 8.6M rows have not been inspected** for what they contain or whether they satisfy any part of D1–D3.
5. **The divergent-implementation finding is unverified by me** — that `call_ephemeris_at_t` and `call_dasha_eligibility` each use their own implementation while the registered engines run only in self-tests. If true it reshapes D8 for several Tier C assets.

---

## 7. Sequencing

| Phase | Work | Gate |
|---|---|---|
| **P0** | Pathfinder: `ka_graha_sancara` end-to-end → **1/22** | Proves the acceptance path; yields the first cost figure |
| **P1** | Run `egate`; reconcile the frozen manifest; fix §6.1 registry/DAG discrepancies through the governed route | Tiers become measured |
| **P2** | Native rules Q1–Q8 | Unblocks century, the three unconsumed assets, and the truncation policy |
| **P3** | Stream A frontier, hubs frozen first | `N/22` moves fastest here |
| **P4** | Streams B and C open once their hubs are frozen; all D1/D2 contract work runs in parallel from P1 | — |
| **P5** | U01–U11 consumer integration and value proof | Needs real accepted data |

**Fan-out condition, unchanged: one real freeze event first.** Parallelising an unproven
acceptance path multiplies the failure — which is exactly what the previous fleet did.
