---
artifact: MADHAV_DATA_PLANE_L1_CURRENT_STATE_AND_DISPOSITION
version: "1.0"
status: PRODUCER_READY
observed_at: 2026-09-14T19:08:09+05:30
source_revision: a9c44c298
execution_base: f6fed12c794224329f6b3b436f8b1b814499d06d
strategy_decision: DP-SD-013
scope: "Source, generated inventory and local synthetic evidence; no private rows, live DB, deployment, serving or value certification."
---

# L1 Gaṇita current state and disposition

## 1. Measurement boundary

The generated census and current wrappers resolve to exactly 19 `ga_*` writers. The
validator maps all 19 to producer source, including the two wrapper exceptions:
`ga_nakshatra` contains inline producer work and `ga_prashna` delegates to
`ga_prashna_writer.py`. `DBURL` and `DATABASE_URL` were absent, so population,
production health and service reachability are `NOT_RUN`; no private row was read.

The historical `ga_chart_service` name is not a twentieth writer. Its current capital is
the computation kernel in `brahmagyan/ganita/engine.py`, `pyjhora_adapter/compute.py`
and the method adapters/routes that call them. Source calls are present and the local
adapter suites pass; deployed reachability was not tested.

State vocabulary: `present` means source/interface exists; `populated`, `served` and
`value_evaluated` require separate evidence. `P/I/E/Q/H` below mean preserve,
interface-contract, elevate, qualify and hold/restrict.

## 2. Complete writer disposition

| Writer | Store and existing natural write grain | Current disposition | Producer-ready result |
|---|---|---|---|
| `ga_positions` | `chart_facts`; chart/ayanāṃśa/category/subject/key/build | P/I/E/Q | Stable fact identity and runtime context/snapshot boundary enforced. |
| `ga_vargas` | `chart_divisionals`; chart/graha/ayanāṃśa/varga/category/key | P/I/E/Q | Build removed from fact identity; formula/domain/boundary sensitivity and exact row grain retained in generation snapshots. |
| `ga_dashas` | `chart_dashas` plus Prāṇa scope fact; chart/ayanāṃśa/system/level/start/build | P/I/E/Q | Deterministic parent-aware UUID5 hierarchy; exact typed composite history is copied set-wise per completed partition and retains post-pass revisions without defeating COPY. Prāṇa is an explicit inapplicable fact, never an invalid level-5 interval. |
| `ga_nakshatra` | `chart_facts`; nakshatra/KP/tara categories at chart context | P/I/E/Q | Inline producer mapped; build removed from fact identity; mean/true-node distinction remains explicit. |
| `ga_panchanga` | `chart_facts`; birth-instant almanac categories | P/I/E/Q | Build removed from fact identity; birth instant remains distinct from arbitrary-day/place service. |
| `ga_sensitive` | `chart_facts`; point/formula/category/subject/key | P/I/E/Q | Build removed while formula remains a real variant; complete geometry/vara is required and day/night is computed against exact sunrise/sunset from validated birth inputs rather than defaulting to 0°/Sunday/day. |
| `ga_sensitive_degree` | `chart_facts`; detector/category/subject/key | P/I/E/Q | Build removed from stable identity; orb/proximity remains evidence, not manifestation. |
| `ga_strength` | `chart_facts`; component/category/subject/key | P/I/E/Q | Build removed from identity; component units retained. Sign-keyed AV remains capital; contributor prastāra remains computed-discarded/unavailable because no named consumer justifies a new payload. |
| `ga_structural` | `chart_facts`; relation/category/actor-target/key | P/I/E/Q | Build removed from identity; complete geometry is validated before every family, so Aries/house-1/longitude-0 defaults cannot enter an emitted generation. |
| `ga_condition` | `chart_facts` plus `ga_condition_composite`; chart/ayanāṃśa/graha | P/I/E/Q | Random atomic IDs replaced by semantic IDs; raw components remain distinct from composite judgment and missingness. |
| `ga_yoga` | `ga_yoga_firings`; chart/ayanāṃśa/rule | P/I/E/Q | Preserved kernel; occurrence contract requires exact qualified rule and explicit clauses/participants. Unqualified source cannot fire positively. |
| `ga_vichara` | `chart_vichara`; chart/ayanāṃśa/varga/subject judgment | P/I/E/Q | Preserved as judged/rule-derived output, not astronomy; no consumer vocabulary rewrite. |
| `ga_sade_sati` | `chart_facts`; cycle/phase/category/key | P/I/E/Q | Build removed from identity; phase/method/frame distinction retained without activation meaning. |
| `ga_transit_anchors` | `ga_transit_anchors`; chart/ayanāṃśa/graha | P/I/E/Q | Requires complete sign/longitude anchors for all nine grahas and Moon; invalid signs and partial output fail closed. |
| `ga_tajaka` | `l1_tajik_varsha_year_lords`; chart/ayanāṃśa/year | P/I/E/Q | Random annual-row identity replaced by deterministic UUID5 over year and return interval; annual clock remains separate. |
| `ga_ayurdaya` | `chart_facts`; method/category/subject/key/build | P/Q/H | Build removed from identity; retained only as restricted scholarly capital, never individualized mortality/lifespan delivery. |
| `ga_medical` | `ga_medical`; chart/ayanāṃśa/graha | P/Q/H | Preserved `not_diagnosis=true` posture; no diagnosis, reassurance or timing activation. |
| `ga_vastu` | `ga_vastu_planet_direction_map`; chart/ayanāṃśa/graha | P/I/Q/H | Preserved traditional direction mapping; explicitly not a complete spatial/building assessment. |
| `ga_prashna` | `ga_prashna_lagna` and `ga_prashna_judgment`; question chart/ayanāṃśa/method | P/E/Q/H | R-1 remains dormant. Natal zero-output is legitimate; no endpoint or method-breadth activation. |

All 19 adapters opt into `l1.data-plane.contract.1.0` without changing WriterBase,
caller-owned transactions, numerical kernels, idempotency scopes or the shared
`SWISS_STATE_LOCK`. Forward-only migration
`1033_data_plane_l1_producer_history.sql` was required because active tables replace rows
and cannot preserve all generations. It adds append-only partition receipts, immutable row
revisions, explicitly specified typed condition facts and quarantined configuration observations
across the 12 L1 output tables, exact/latest-generation selectors and reversible head
selection; it does not rewrite an existing table or backfill invented history.

## 3. Consumer backcast and gaps

Read-only search found active source projections for `chart_facts`,
`chart_divisionals`, sensitive degrees, medical, Vāstu and yoga firings, plus L2-L4
consumers and generated digest dependencies. These prove code demand, not successful
runtime consumption. The principal offer is now a typed producer envelope with exact
context, stable IDs, missingness, epistemic class, generation and source dependencies.

Demand findings intentionally left for later authorized stages: some consumers still
flatten producer values, use date-level clocks, locally re-derive fields, or omit complete
context/generation checks. Retrieval, L2-L5, Paripraśna, synthesis and MCP were read only.

| Truth dimension | Final L1 evidence |
|---|---|
| Present | YES — 19 wrappers and source mappings. |
| Populated | `NOT_RUN` — no live DB credential. |
| Qualified | YES — local contract/PostgreSQL proof and final independent review pass with zero HIGH/MED/LOW findings. |
| Consumed | Source callers found; operational consumption not proved. |
| Effect traced | NO — later-layer responsibility. |
| Served | NO current operational claim. |
| Value evaluated | NO. |

## 4. Historical finding disposition

Stable identity defects in 12 producer locations and random condition/dasha/Tājaka IDs
were current and are fixed at `7cabc0cfd`. Runtime adoption, append-only replay/history,
Prāṇa scope-cap and numerical fallback findings from the first independent challenge are
corrected at `3cb1a84ae`. Its follow-up challenge found multi-partition generation,
completed-generation freeze/latest-row, typed projection, broad non-finite, sensitive
day/night and slice dependency/D9-sensitivity gaps; all are corrected at `bcda11997`.
The next re-challenge found dasha receipt/capture coupling, asset-level field semantics and
catastrophic high-volume fact fan-out. Commit `0fc45813e` separates receipts, applies an
explicit condition-field registry with actual constituent identities, quarantines yoga
catalog observations with exact content digests and typed roles, and records dasha history
through a bounded typed composite partition copy. That re-challenge found volatile dasha
replay/digest inputs, cross-context condition dasha
selection and cross-ayanāṃśa/date-truncated concurrency. Commit `b2c4f1d7f` introduces one
canonical build/time-independent dasha payload with stable hierarchy identities, scopes
condition ancestry to exact ayanāṃśa/build, and evaluates concurrency only inside the same
ayanāṃśa using exact instants. An interim final re-challenge then found nested source build
identity leaking into condition
semantics. Commit `a9c44c298` retains build in the enclosing observation context while
keeping stable dasha row and ayanāṃśa identities in the semantic period dependency. Final
independent review of exact tip `a9c44c298` returned PASS with zero HIGH, MED or LOW
findings. Precise clock
hierarchy and sign-keyed AV are
preserved capital. Contributor prastāra is accurately `unavailable`, not “no AV”. Numerical
fallback is covered by failure-state negative proof. Specialized restrictions remain current
and enforced by scope. Historical freezes/receipts remain bounded evidence and were neither
reopened nor mutated.
