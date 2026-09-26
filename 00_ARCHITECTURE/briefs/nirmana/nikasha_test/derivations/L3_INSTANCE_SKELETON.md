---
artifact: L3_INSTANCE_SKELETON
canonical_id: L3_INSTANCE_SKELETON
status: TEST ARTEFACT — NOT AN INSTANCE
pilot: yes
campaign: nikasha-test, Phase 4
produced_on: 2026-09-26
derived_from:
  - tiers 1-2 via 00_ARCHITECTURE/briefs/nirmana/nikasha_test/derivations/_tier1_tier2_summary.md
  - tier 3 (SEALED): 00_ARCHITECTURE/briefs/nirmana/LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md
  - census: 00_ARCHITECTURE/briefs/nirmana/nikasha_test/census/L3_sandbox_20260926.json  # SANDBOX RUN — no L3_prod_20260926.json exists (only L3_prod_20260926.log). All census figures below are sandbox figures, noted as such.
---

# L3 Kāla — INSTANCE SKELETON · TEST ARTEFACT — NOT AN INSTANCE

`INVENTED — <what>, clause that should have provided it: <quote>` marks every place the tiers + census
did not supply the content and the fresh reader had to fill it.

## Part 0 · VALUE

### 0.1 · What cannot be answered without this layer

```
inherits:    Product §2 (P01-P24), Data plane §2 (V01-V13)
measured_by: none — definitional; but every P/V cited must exist in the parent under current numbering
traces_to:   —  (this IS the origin)
```

Provided by tiers: L3's row exists in Product §11 ("Which structures are engaged by which clocks, when,
under what conditions and with which alternatives") and DP08 names "the present-tense need (P24) the
interval now active and the one immediately preceding it", and the tier-2 summary maps V13 = P24
present interval. **No per-layer P-need / V-journey assignment exists anywhere in tiers 1–2**; the
P01–P24 table and the V01–V13 table are not keyed to layers.

INVENTED — the necessity rows themselves (which P/V rows L3 is *necessary* to). Clause that should have
provided it: template §0.1 "List the P-needs and V-journeys for which this layer is **necessary**" —
the template demands the list but neither sealed parent assigns P-needs or V-journeys to layers, so
only P24/V13 are document-anchored; every other row below is reader judgement.

| P / V | the distinction that disappears without this layer |
|---|---|
| P24 / V13 (document-anchored via DP08) | which interval is active NOW and which immediately preceded it, each with engaged participants |
| INVENTED — timing P-needs (e.g. "when might I initiate something" per P11's temporal half) | no clock tells when a structure is engaged; all timing questions degrade to static structure |
| INVENTED — V-journeys involving period/act phases | no daśā/gochara/varsha window can be named |

### 0.2 · The layer's objective

```
inherits:    Product §1 (the join), §11 (L3 row), Data plane §3.1 (L3 row)
measured_by: none — definitional
traces_to:   0.1
```

Derivable without invention from sealed parents:

- **Owned question** (data plane §3.1): "Which of those structures are engaged, how, when and under
  what conditions?"
- **Hands onward**: "Structure–time mechanisms, background/enablement/contact/inhibition intervals,
  recurrence, comparisons and coverage-qualified windows."
- **Must not claim**: "Activity/intensity as event probability; precise geometry as equally precise
  life timing."
- **Scored on** (Product §11 L3 row): **Temporal integrity** — "nearest versus better-supported under a
  named criterion; honest 'none found' semantics."

INVENTED — "what it computes that existing software does not" and "what it hands the reasoning layer to
read across". Clause that should have provided it: template §0.2 "Name what it computes that existing
software does not, and what it hands the reasoning layer to read across." — no parent text compares L3
to existing software; any such sentence is authored, not derived.

### 0.3 · Its place in the wheel

```
inherits:    Data plane §3.2 (five edge types), §7 (DP contracts)
measured_by: registry depends_on reconciled across seed, migration pin AND live asset_registry — state all three and any disagreement
traces_to:   0.2
```

Derivable from tier 2 §7.1: **consumes** DP05 (configuration, L0+L1→L2→L3), DP06 (structural
relationship, L2→L3), DP07 (precise clocks/contacts, L0/L1/L3 primitives); **produces** DP08 (temporal
mechanism, "L2+qualified clocks → L3 consumers").

From census (sandbox): intra-plane edges resolvable for all 23 assets (Build.dag PASS, 0–11 edges
each); cross-layer deps visible in Build.history text (`ga_dashas`, `bo_*`, `bg_sarvatobhadra_grid`).

INVENTED — (a) the seed and migration-pin two of the three required reconciliation sources: the census
carries no seed/pin read. Clause: template §0.3 `measured_by:` "registry depends_on reconciled across
seed, migration pin AND live asset_registry — state all three and any disagreement". (b) the **edge
type** of each edge (definition/computational/serving-context/evaluation/next-generation): the census
reports edge counts, never types. Clause: template §0.3 "Receives from: upstream layers, **by edge
type**, by DP contract" — no instrument or parent table assigns edge types per asset edge.

## Part 1 · VALUE DECOMPOSITION (only 1.1 required by the assignment)

### 1.1 · Inventory, measured

```
inherits:    Data plane §13.3 item 2
measured_by: asset_registry (live, read-only) · the registry seed · the migration-governed pin · asset_throughput · the production probe
traces_to:   0.3
```

Census (sandbox, 2026-09-26) provides: **23 assets**, `registered_ids: 11` vs `registry_has_writer: 23`
— i.e. **12 assets the registry declares writer-backed with no `@register` found** (`Build.registered`
FAIL on ka_dasha_kala, ka_gochara_resonance, ka_gochara_sweep, ka_gochara_v3_century_materialize,
ka_kota_chakra, ka_kshetra, ka_moorti_nirnaya, ka_muhurta_seva, ka_sudarshana_varsha, ka_tithi_pravesha,
ka_tulana, ka_vedha_gochara). `never_exercised_with_writer: []`; `local_map_candidates: -1` (no
detector). One RETIRED asset (ka_gochara_sweep). Four services (`target_table` null, asset_kind
'service'): ka_dasha_kala, ka_graha_sancara, ka_muhurta_seva, ka_tulana.

INVENTED — (a) `live_rows`: `null` for all 23 assets in the census; the row figures used below come
from `Complete.depth` over the **sandbox sample**, not each asset's own count_sql against production.
Clause: template §1.1 `measured_by:` "the production probe (asset_elevation_tracker.py --layer <L>
--env-file)" — the sandbox census is not the production probe. (b) **floors and Δ against floor**:
the census carries no floor field. Clause: tier-4 template §1 "rows by the asset's own `count_sql` …
floor, delta" (inherited into 1.1). (c) **column-level truthfulness of count_sql/target_table**:
census gives PASS on Build.target but never tests that count_sql's population matches target_table
for shared tables.

| asset | table (census) | sandbox rows (Complete.depth) | writer file | notes |
|---|---|---|---|---|
| ka_avadhi | kala_avadhi | 3620 | ka_avadhi.py | history FAIL (UndefinedColumn d.dasha_start) |
| ka_bhavishya_lekha | kala_bhavishya | 100 | ka_bhavishya_lekha.py | dep_liveness FAIL |
| ka_dasha_kala | — (service) | n/a | NONE | registered FAIL |
| ka_gochara | kala_gochara_windows | 40117 | ka_gochara.py | **shares table with ka_gochara_sweep** |
| ka_gochara_resonance | gochara_resonance_map | 1595 | NONE | registered FAIL |
| ka_gochara_sweep | kala_gochara_windows | 40117 (same table) | NONE | RETIRED; shared table |
| ka_gochara_v3_century_materialize | kala_gochara_windows_v2 | 1993 | NONE | registered FAIL; history FAIL |
| ka_graha_sancara | — (service) | n/a | ka_graha_sancara.py | Idem PARTIAL (delegates) |
| ka_jivana_parva | kala_jivana_parva | 309 | ka_jivana_parva.py | dep_liveness FAIL |
| ka_kala_darshana | kala_darshana | 750 | ka_kala_darshana.py | dep_liveness FAIL |
| ka_kalasutra | kala_activation | 16925 | ka_kalasutra.py | dep_liveness FAIL (ka_sangam) |
| ka_kota_chakra | kala_kota_chakra | 1170 | NONE | registered FAIL |
| ka_kshetra | kala_field | 549797 | NONE | registered FAIL; history FAIL (98 errors) |
| ka_moorti_nirnaya | kala_moorti_nirnaya | 143 | NONE | registered FAIL |
| ka_muhurta_seva | — (service) | n/a | NONE | registered FAIL; 0 deps |
| ka_sangam | kala_convergence | 20497 | ka_sangam.py | 11 edges |
| ka_sudarshana_varsha | kala_sudarshana_varsha | 120 | NONE | registered FAIL |
| ka_taranga | kala_taranga | 13963 | ka_taranga.py | dep_liveness FAIL |
| ka_tithi_pravesha | kala_tithi_pravesha | 240 | NONE | registered FAIL |
| ka_tulana | — (service) | n/a | NONE | registered FAIL; dep_liveness FAIL |
| ka_vedha_gochara | kala_vedha_gochara | 355 | NONE | registered FAIL |
| ka_vighnakara | kala_obstruction | 747 | ka_vighnakara.py | dep_liveness FAIL |
| ka_yojaka | kala_activation_predicates | 7525 | ka_yojaka.py | 7 edges |

**Shared-table finding (C-10/R06/R10 confirmed for L3):** `kala_gochara_windows` has TWO registry
producers — ka_gochara (CURRENT) and ka_gochara_sweep (RETIRED) — and the census's `Complete.depth`
credits each with the same 40,117 rows. Clause that should have provided for this: template §1.1
"For each: target table(s) — a **set**, not one pointer, for multi-table assets — row counts in
production" — the registry/census model is one `target_table` string per asset and cannot express
*several producers of one table*; there is no partition key declared to separate their rows.

## Part 2 · CONDITIONS

### 2.1 · Correctness rules

```
inherits:    Product §8.1 (L3 row), §13; Data plane §9.2 (the switch and the storage separation)
measured_by: a detector per rule, named here, that can report the rule violated
traces_to:   0.2
```

Provided verbatim (Product §8.1, L3 row): "**Using the observed event to choose the supposedly prior
trigger.**" Plus §13: no invented computation/source/detector/confidence/score.

INVENTED — the per-rule detectors. Clause: template §2.1 "**For each rule, the detector.** A rule with
no detector is a wish." — no parent names a detector for the L3 switch rule, and the census has no
check for it; stating one (e.g. "no L3 writer may read an observation table") is reader-supplied.

INVENTED — the switch ON/OFF behaviour per asset and its storage separation. Clause: template §2.1
"The life-event switch: what this layer may do when ON, what it emits when OFF, and the storage
separation that makes OFF a selection rather than a rebuild." — data plane §9.2 is cited in the
inherits line but its L3-specific content is not stated in any tier-1/2 text available to the reader.

### 2.2 · Presentation obligation

```
inherits:    Product §2 (two modes, one depth); Data plane §3.4 (field → contract mapping)
measured_by: presentation-parity test (Data plane §12.2)
traces_to:   0.1
```

Partially provided: data plane §3.4 maps "clock geometry/activation/manifestation bridge → DP07/DP08/DP09"
and template §2.2 names the temporal row's fields ("clock geometry, activation rule, the named
criterion, the bridge or falsifier").

INVENTED — the full list of §3.4 rows L3 carries. Clause: data plane §13.3 item 6 "…**including which
§3.4 presentation rows this layer carries and which fields it hands onward for them**" — §3.4's
carriage assignment maps rows to DP contracts, not to layers; beyond the temporal row, whether L3 also
carries method/school (DP02) or conventions (DP01/DP03) for its findings is unassigned.

NOTE (TRANSFERS finding): the parity test this section demands is data plane §12.2's **Presentation
parity [TRANSFERS]** row, while tier 2 §1 rules "A [TRANSFERS] obligation is not a data-plane layer's
to build alone, and a layer plan does not inherit it as its own work." Yet layer template §5.4 test 4
makes "Presentation parity holds for the layer's served surface" an **acceptance test of this
instance**. A layer plan cannot tell whether parity is its own work — the two sealed documents assign
the same obligation to different owners.

### 2.3 · Contracts produced and consumed

```
inherits:    Data plane §7 (DP01-DP17), §7.1 (common envelope)
measured_by: for each contract, the fields and grain actually present in the producer's table and actually read by the consumer — verified both ends
traces_to:   0.3
```

Provided (tier 2 §7.1): L3 **produces DP08** (temporal mechanism, incl. the P24 present+preceding
interval pair); **consumes DP05, DP06, DP07**.

INVENTED — field/grain/identity per contract and the "declared use" of every consumed input. Clause:
template §2.3 "Every consumed input declares its use — calculation, applicability, counter-evidence,
uncertainty, interpretation, exclusion, navigation, evaluation. **A citation with no declared use is
not a contract.**" — the census never records fields, grain, or declared use; no parent gives L3's
per-contract field lists.

### 2.4 · Jyotish coverage owned

```
inherits:    Product §3 (substance), Data plane §5 (domain obligations)
measured_by: per obligation: applied / inapplicable-with-reason / unavailable / unqualified / unresolved — the five states, never a blank
traces_to:   0.1
```

Provided (Product §3, in substance): the Kāla instrument list — daśā, gochara, aṣṭakavarga/vedha,
Tājaka, tithi-praveśa, Sudarśana.

INVENTED — the five-state verdict per obligation. Clause: template §2.4 `measured_by:` "per obligation:
applied / inapplicable-with-reason / unavailable / unqualified / unresolved — the five states, never a
blank" — the census measures table depth, not coverage states; no instrument exists that maps assets
to these §5 states. Census also shows `Complete.width: NOT_GENERIC` for all 23 assets — "no declared
universe for this asset" — so even width is unmeasurable as specified.

### 2.6 · Vocabulary conformance

```
inherits:    Data plane §4.1 (the controlled vocabulary — six rules with detectors)
measured_by: alias-set coverage per entity class · independent-map census per class · interface-parameter census · parity-test presence
traces_to:   0.2
```

INVENTED — which of the sixteen entity classes L3 emits or accepts. Clause: template §2.6 "Which of the
sixteen entity classes this layer emits or accepts; for each, whether every name resolves through the
controlled set…" — no parent assigns classes per layer, and the census's only related instrument
returns `local_map_candidates: -1` (detector absent / not run). A plausible list (dasha_system,
event_class, concept, school) would be reader-supplied.

### 2.7 · Source carriage and reproduction

```
inherits:    Product §11; Data plane §12.2 (Source carriage and reproduction), §4.3, §5
measured_by: the three checks below, each named per obligation this layer owns, each able to return false
traces_to:   0.1
```

Census verdict for ALL 23 assets: `Carr.detector: NO_DETECTOR` — "no D1/D2/D3 detector exists for this
asset; which check applies is per-asset semantics".

**C-9 / R09 CONFIRMED for L3.** Template §2.7 assigns the a/b/c checks "per obligation this layer owns"
(layer scope); §4.4 row 13 demands them per asset. Nothing in the tier chain assigns a carriage check
to any individual L3 asset, so all 23 would have to be chosen by the brief author. Clause: template
§4.4 "**the relevant Jyotish concepts** the asset touches, named, with the domain detector each invites
(2.7, 5.2's menu)" — the clause presumes an assignment the template's own §2.7 does not produce.

### 2.5 · Edges and order

```
inherits:    Data plane §3.2; the registry DAG
measured_by: topological sort of the reconciled depends_on from 0.3; cycle check; cross-layer gates via egate.sql scoped to the CURRENT frozen definition revision
traces_to:   0.3
```

Census provides per-asset edge counts (0–11) and resolvability (all PASS), plus dep_liveness failures
naming ka_sangam, ka_vighnakara, ka_kala_darshana, ka_kalasutra as not-lit dependencies (sandbox).

INVENTED — (a) the topological order itself (census gives counts, no sort); (b) cross-layer gate state
against "the CURRENT frozen definition revision": egate.sql was not run by the census and no frozen
definition revision exists for L3. Clause: template §2.5 `measured_by:` "cross-layer gates via
egate.sql scoped to the CURRENT frozen definition revision" — no such revision exists to scope to.

## §4.4 · What each asset brief inherits — the thirteen rows

```
inherits:    Product §16; Data plane §13.3 (asset brief sentence)
measured_by: derivability
traces_to:   0.1
```

| # | row | derivable for L3? |
|---|---|---|
| 1 | P-needs / V-journeys (0.1 narrowed) | PARTIAL — P24/V13 anchored; the rest INVENTED (see 0.1) |
| 2 | obligations scored on (0.2) | YES — Temporal integrity (Product §11 L3 row) |
| 3 | correctness rules + switch behaviour (2.1) | PARTIAL — rule verbatim YES; switch behaviour + detectors INVENTED |
| 4 | presentation fields (2.2) | PARTIAL — temporal row named; full §3.4 row set INVENTED |
| 5 | contracts produced/consumed + declared use (2.3) | PARTIAL — DP05/06/07 in, DP08 out named; fields/grain/use INVENTED |
| 6 | coverage obligations + current states (2.4) | PARTIAL — obligation list from Product §3; states NOT MEASURED (no instrument) |
| 7 | order + three-way baseline (2.5, §4.1) | PARTIAL — edge counts only; no sort, no baseline (census is sandbox; no current-code read) |
| 8 | disposition + must-add (3.2/3.3) | INVENTED — no Part 3 content derivable without a measured Part 1. Clause: template §3.2 "For every asset and service in 1.1, one of the data plane's eight dispositions, with the evidence from Part 1 that justifies it" |
| 9 | individual term (1.2) | NOT MEASURED — no ablation harness; template permits "unmeasurable — not reached" (§1.2) |
| 10 | synergistic term (1.3) | NOT MEASURED — absent instrument; template permits recording seam-by-seam instead |
| 11 | cross-layer term (1.4) | PARTIAL — DP08 produced named; evidence state per consumer unverified |
| 12 | preserved kernel (3.2) | INVENTED per asset — no tier text or census field defines any asset's kernel. Clause: template §4.4 "**the preserved kernel** — what of the asset must survive any rebuild unchanged (from 3.2)" — §3.2 is dispositions, which themselves were never derived |
| 13 | Jyotish concepts + carriage check (2.7/§4.4) | INVENTED per asset — C-9/R09 CONFIRMED (see 2.7) |

**Reference-layer / chart-product check:** L3 is `scoring: contribution` (census). The template's
reference-layer clauses (§1.2, §5.1, "never R for lack of a reader") correctly do not fire here. The
chart-product-only machinery that MISFITS L3's edge kinds: the `Idem` convention "L1+ delete-then-insert
scoped to (chart_id × natural key)" (tier-4 §4 Idem row) presumes a table and a chart grain — L3's four
services have neither, and the census itself N/As their Build.target; the template gives no service
idempotency convention. Also global-build coverage: 67 global runs touch the layer 551 times (census),
so unlike L0 the global path exists for L3 — but the tier-4 §4.2 note "L0's proving path is not the
global one" is the only per-layer build-path guidance; nothing states which scope an L3 layer plan
claims. Clause: tier-4 §4.2 "a layer plan must say which scope it is claiming. For L1–L5 the global
path is the one that matters" — stated, so NOT an invention; recorded as provided.
