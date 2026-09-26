---
artifact: BG_PANCHANGA_ELEVATION_BRIEF
canonical_id: BG_PANCHANGA_ELEVATION_BRIEF
tier: 4
kind: instance
version: "1.0"
status: PILOT_DRAFT
produced_on: 2026-09-26
template: 00_ARCHITECTURE/briefs/nirmana/ASSET_ELEVATION_TEMPLATE_v2_0.md
layer_instance: 00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v3_0.md
pilot: yes
role_in_pilot: "4 of 5 — a SERVICE with no table by design. Stresses whether the template disposes honestly instead of inventing rows to count."
measured_on: 2026-09-26
measured_against: "live asset_registry · asset_throughput · the 4 capability modules referencing panchanga"
verdict: NONE
---

# bg_panchanga — asset elevation brief (pilot 4 of 5)

**Headline: the template disposes of a table-less asset honestly — six of eight gates are N/A with
reasons — and the one thing a service needs, a service proof, has no detector.** `asset_throughput` says
`state=lit, rows_written=0`: correct for a service, and indistinguishable from a failed build. That
ambiguity is the finding.

## §0 · Identity and inheritance

```
asset_id: bg_panchanga · layer: L0 Brahmagyan · pilot: yes
kind: SERVICE — no table by design · scoring_mode: fidelity · role: neither
measured_on: 2026-09-26
```

### 0.1 · Inherited — thirteen rows

| # | what | value |
|---|---|---|
| 1 | P/V | **P21** (what does this day or period mean in its proper context) directly; **P11** (initiation) and **V05** (calendar and method selection) |
| 2 | obligations | **operational honesty** (primary for a service — earned status, recovery under failure) · computational correctness · delivery fidelity. **Not** source fidelity: it testifies to nothing |
| 3 | correctness + switch | no per-subject storage at all (it stores nothing); switch-irrelevant |
| 4 | presentation fields | the §3.4 "conventions in force" row — a pañcāṅga answer must carry date, location and time-zone convention with it |
| 5 | contracts | **produces** the calendar substrate consumed by L1 (`ga_*`, 1 declared registry edge); consumes `bg_ephemeris` positions in effect, though no registry edge declares it |
| 6 | coverage owned | the calendar half of the §5 Praśna/Muhūrta/calendar row |
| 7 | position + baseline | root in the registry (0 declared dependencies — itself a finding, since it cannot compute without the ephemeris); deployed = current code · **risk 0** |
| 8 | disposition | **P — preserve**, with one E item (a service proof) |
| 9 | fidelity | **NOT APPLICABLE as row-fidelity** — there are no rows. Fidelity for a service = it answers, correctly, with its conventions attached. **No detector exists**, so: unmeasured |
| 10 | synergistic | it is the seam between the ephemeris and every calendar-shaped question; undeclared in the registry |
| 11 | cross-layer | 1 declared consumer (Gaṇita); 4 capability modules reference pañcāṅga |
| 12 | **preserved kernel** | the service interface and its convention handling — there is no data to preserve |
| 13 | **concepts + carriage check** | it computes calendar quantities → **D3 independent re-derivation** (a tithi or vāra recomputed a second way). D1 N/A, D2 N/A. *Chosen here — C-9.* |

### 0.2 · What it is for
It turns an instant and a place into the tradition's calendar: tithi, vāra, nakṣatra, yoga, karaṇa. It holds
nothing, so it can only be judged by whether it answers correctly — which is precisely why a service needs a
different proof from a table.

## §1 · Measured current state

- **Storage: none, by design.** `target_table` NULL, `count_sql` empty, `has_writer` false, no
  `integrity_check_sql`. All four absences are correct for this asset kind and are recorded as such so
  they are never read as missing work.
- **Producer:** no orchestrator writer — correct. The service lives in the sidecar's pañcāṅga routes.
- **Consumers:** 1 declared registry edge (Gaṇita); **4 capability modules** reference pañcāṅga, including
  `call_panchanga_service.ts` and `intent_classify.ts`.
- **Build cost / state:** `asset_throughput`: `state=lit, rows_written=0, rows_per_second=NULL,
  last_built_at=2026-08-27`. For a service, `rows_written=0` is the truth — **and it is the same value a
  failed table build would write.** The build-state surface cannot distinguish "service, nothing to write"
  from "writer ran and produced nothing".
- **Three-way baseline:** deployed = current code; **risk 0**.
- **Evidence state:** source-present N/A · qualified ✓ (conventions declared) · consumed ✓ · transformed ✓
  · served ✓ (4 modules) · value-evaluated ✗.

### 1.1 · Completeness — width and depth
**Not a row census — a capability census, and it is the honest mapping of this section to a service.**
Width = the five pañcāṅga limbs (tithi, vāra, nakṣatra, yoga, karaṇa): the forensic anchors that this
project's own birth-data check verifies include four of the five, so the limbs are computed. **Depth** =
each limb returned with its convention, boundary and precision. **NOT MEASURED** this pass: no census of
the service's response fields was run. Recorded as a gap, not assumed complete.

### 1.2 · Reachability
4 capability modules; **field-level census NOT MEASURED**. For a service the reachability question is
whether every limb and its convention are exposed, not whether rows paginate. Requirement **[TRANSFERS]**.

## §3 · Obligations specialised

| obligation | satisfied means | detector |
|---|---|---|
| Operational honesty | the build-state surface distinguishes a healthy service from a failed writer | **none** (G01) |
| Computational correctness | a limb recomputes a second way and matches | D3 — **does not exist** (G02) |
| Delivery fidelity | every limb reaches a caller with its convention attached | the §1.1/§1.2 censuses — **not run** (G03) |

## §4 · The eight gates — six N/A, each with its reason

| gate | verdict | reason / detector |
|---|---|---|
| **Ldgr** | **N/A** | no rows, so no derived value to trace to an upstream id. Not "unchecked" — inapplicable by asset kind. |
| **Idem** | **N/A** | writes nothing; a rebuild has nothing to replace or accrete |
| **Earn** | **FAIL** | the asset's only status is `asset_throughput.state='lit'` with `rows_written=0` — a signal that reads identically for a healthy service and a writer that produced nothing. A service needs a liveness/correctness signal that could return false; none exists. |
| **Null** | **N/A** | emits no stored values. (Its *responses* should distinguish unavailable from inapplicable — untested, folded into G03.) |
| **Vocab** | **PARTIAL** | it emits limb names and weekday/tithi vocabulary; whether those resolve through the ontology's closed set was **not measured** — the census the rule requires does not exist for service responses |
| **Carr** | **NO_DETECTOR** | D3 applies (recompute a limb a second way). Nothing does. |
| **Narr** | **N/A** | emits structured limbs, not prose |
| **Dens** | **N/A** | serves single-instant answers; no paginated or faceted row set to layer. Declared here so the N/A is a disposition, not a silence. |

**This is the pilot's main template result: a table-less asset is expressible without inventing a single
row.** Four registry absences and six gate N/As all carry reasons; nothing had to be faked to make the
brief look complete.

## §5 · Ledger rows (registered)
`G01` build-state cannot distinguish service from failed writer · `G02` no D3 limb re-derivation ·
`G03` no response-field census (completeness and reachability both unmeasured) · `G04` the ephemeris
dependency is real and undeclared in the registry. Opportunity `O1`.

## §9 · Opportunity register

| id | dimension | what it would add | proposal | proof afterward |
|---|---|---|---|---|
| `O1` | **architecture** | a service kind the build system can judge | Give service assets their own state vocabulary — a liveness+correctness probe (answer a pinned instant, compare to a stored expected limb set) instead of `rows_written`. Cost: one probe per service asset. Risk: none. This is a **layer-level** proposal: L0 has 2 service assets and other layers have more. | the probe fails when the service is down or wrong, and `state` no longer reads `lit` for a broken service |
| `O2` | **synergy** | a declared edge where a real one exists | declare `bg_panchanga → bg_ephemeris` in the registry: the service cannot compute without positions, and the DAG says it is a root | the registry DAG matches the actual computation path |

## §6 · Change packet — not authorised here
```
may_touch:      the panchanga service module · a new service probe · the registry edge
must_not_touch: pipeline/orchestrator/** · any applied migration
base:           5973d0132
```
Preserved kernel: the service interface and its convention handling. Rollback: none needed (no data).

## §2 · Shape
identity ✓ inputs/DAG ✓ correctness ✓ data sufficiency ✓ (as a capability census) consumers ✓
value/target ✓ synergy ✓ knowledge-time ✓ change packet ✓ evidence ✓

## §7 · Certification — none (pilot)
## §8 · Review — unsigned. **Derivability: 12 of 13 (C-9). Plus one template finding: §1's storage bullets assume a table; a service fills them with four honest N/As, which worked, but the template should say so explicitly rather than leaving each author to decide.**
