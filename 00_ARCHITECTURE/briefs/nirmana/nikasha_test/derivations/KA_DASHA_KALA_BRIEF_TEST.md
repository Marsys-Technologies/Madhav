---
artifact: KA_DASHA_KALA_BRIEF_TEST
canonical_id: KA_DASHA_KALA_BRIEF_TEST
status: TEST ARTEFACT — NOT A BRIEF
pilot: yes
campaign: nikasha-test, Phase 4
produced_on: 2026-09-26
template: 00_ARCHITECTURE/briefs/nirmana/ASSET_ELEVATION_TEMPLATE_v2_0.md
layer_instance: 00_ARCHITECTURE/briefs/nirmana/nikasha_test/derivations/L3_INSTANCE_SKELETON.md (TEST ARTEFACT — NOT AN INSTANCE)
measured_against: "census L3_sandbox_20260926.json — SANDBOX RUN, not production"
verdict: NONE
---

# ka_dasha_kala — asset brief TEST ARTEFACT (pilot: yes)

Edge-kind asset: **service, no table by design** — and a broken one. Census (sandbox):
`target_table: null`, `asset_kind='service'`, `has_writer: true` in the registry but **no @register
found and no writer file** (Build.registered FAIL — registry/code disagreement, the three-source rule's
finding), 104 runs across all four scopes (so run history says it IS dispatched — three sources read:
registry YES, code NO, history YES), `rows_written=0`, count_integrity PARTIAL (no count_sql),
dep_liveness PASS (1 edge: ga_dashas), Dens FAIL (2 modules, 0 density_contracts), history PARTIAL
(latest complete; 6 errors / 8 aborts; blocked-on-ga_dashas records).

## §0 · Identity and inheritance

```
asset_id: ka_dasha_kala · layer: L3 Kāla · pilot: yes
kind: service (no table by design) · scoring_mode: contribution · role: temporal
measured_on: 2026-09-26 (sandbox census)
```

### 0.1 · Inherited — thirteen rows (invention record; §8-style)

| # | value | filled from | invented? |
|---|---|---|---|
| 1 P/V | P24 / V13 (present interval is a daśā question) | tier2 DP08 | partial — **INVENTED** beyond P24/V13. Clause: layer §0.1 "List the P-needs and V-journeys for which this layer is **necessary**" (no per-layer P/V mapping in tiers 1–2) |
| 2 obligations | Temporal integrity | Product §11 L3 row | NO |
| 3 correctness + switch | §8.1 L3 rule verbatim | Product §8.1 | NO for rule; **INVENTED** — switch behaviour and detector for a *service*. Clause: layer §2.1 "For each rule, the detector. A rule with no detector is a wish." |
| 4 presentation fields | the temporal row (clock geometry, activation rule, named criterion) | layer §2.2 | **INVENTED** — which output fields of the service carry them. Clause: data plane §13.3 item 6 "which §3.4 presentation rows this layer carries and which fields it hands onward for them" |
| 5 contracts | consumes DP07 (clock primitives); produces DP08 input | tier2 §7.1 | **INVENTED** — per-asset contract rows; a service produces no table, and no clause says how a *service* "produces" a DP contract. Clause: layer §2.3 "Two tables: DP contracts this layer **produces** (consumer, fields, grain, identity, generation)…" — the prescribed shape presumes a table with fields and grain |
| 6 coverage | daśā clocks | Product §3 | **INVENTED** — five-state verdicts; no instrument. Clause: layer §2.4 five-states `measured_by:` line |
| 7 position + baseline | 1 edge (ga_dashas), resolvable; 104 runs | census | **INVENTED** — topological position and three-way baseline. Clause: layer §4.1 "State the three-way baseline per asset: deployed … current code … target" |
| 8 disposition + must-add | E — the registry row and the missing writer must be reconciled | reader judgement on 3-source disagreement | **INVENTED.** Clause: layer §3.2 "one of the data plane's eight dispositions, with the evidence from Part 1 that justifies it" |
| 9 individual term | NOT MEASURED — no ablation harness; a service cannot be ablated by row-removal | layer §1.2 | partial — **INVENTED** — what "ablate one" even means for a table-less service. Clause: layer §1.2 "the reading with it against the reading without it" presumes a removable *asset*, but the removal procedure for a service (deregister the module? fence the endpoint?) is undefined |
| 10 synergistic term | NOT MEASURED — absent instrument | layer §1.3 permission | NO (honest null) |
| 11 cross-layer term | serves 2 modules (call_service_wrappers.ts, index.ts) | census Dens.served | **INVENTED** — evidence state at consumer, unverified. Clause: layer §1.4 "verified at the consumer, not asserted by the producer" |
| 12 preserved kernel | the dispatch contract and the ga_dashas read | reader judgement | **INVENTED.** Clause: layer §4.4 "**the preserved kernel** … (from 3.2)" — undefined for a service whose kernel is behaviour, not rows |
| 13 concepts + carriage check | daśā computation → author chose **D3** (daśā boundaries re-derivable); D1/D2 N/A | CHOSEN BY AUTHOR | **INVENTED — C-9/R09 CONFIRMED (6th confirmation).** Clause: layer §4.4 "**the relevant Jyotish concepts** the asset touches, named, with the domain detector each invites" |

### 0.2 · What it is for
INVENTED prose: the daśā-clock service — answers "which period runs now / next" without a stored table.
The registry/history say it is load-bearing (104 runs); the code says it does not exist. That
disagreement *is* the asset's current state.

## §1 · Measured current state (sandbox census only)

- Storage: none by design — four honest N/As, as pilot 4 (bg_panchanga) established.
- Producer: **registry declares has_writer=true; no @register, no writer file.** Three-source rule:
  registry YES · code NO · run history YES (104 dispatches). The disagreement is the finding.
- Consumers: 2 capability modules; 0 density_contracts.
- Build cost: `Cost.baseline FAIL` — rows_written=0, rps=NULL. NOTE (known defect, pilot 4):
  "rows_written = 0 reads identically for a healthy service and a writer that produced nothing."
- INVENTED — the service's actual behaviour surface (endpoint, signature). Clause: tier-4 §1 "Producer:
  … or 'service'" — the template names the word and nothing the word must carry (no service descriptor,
  no endpoint census).

### 1.1 / §1.2 — N/A by kind (no table → no width/depth census). INVENTED — the template's own
completeness question for a service. Clause: tier-4 §1.1 "a census against a DECLARED universe" —
undefined for an asset with no rows; pilot 4's N/A convention had to be invented by that author too.

## §2 · Shape — identity ✓ inputs/DAG ✓ correctness ✓ data sufficiency ✓ (as N/A-with-reason)
consumers ✓ value/target ✓ synergy ✓ knowledge-time ✓ change packet ✓ evidence ✓

## §3 · Obligations specialised — authored, not derived (see ka_kalasutra §3 note).

## §4 · Nine gates (from census; sandbox verdicts)

| gate | verdict | evidence (census) |
|---|---|---|
| Ldgr | N/A — service derives no rows | kind-implied; the N/A reason had to be authored |
| Idem | N/A | "no writer file" |
| Earn | FAIL | rows_per_second=NULL, last_built=2026-09-11 |
| Null | NOT MEASURED | no inspector check exists |
| Vocab | NOT MEASURED | no table to test identity on; whether a service's output vocabulary is tested is undefined — INVENTED if answered. Clause: tier-4 §4 Vocab row "one canonical id per thing, one closed alias set" is table-oriented |
| Carr | NO_DETECTOR | D3 chosen by author (C-9); none exists |
| Narr | N/A | emits no prose (author judgement) |
| Dens | FAIL | 2 modules, 0 density_contracts |
| Build | FAIL | registered FAIL (registry says writer, code disagrees); contract N/A; target N/A; dag PASS; count_integrity PARTIAL; exercised PASS (104 runs); history PARTIAL |

## §5 · Delta ledger — implied rows: Build.registered (three-source disagreement), Earn, Cost, Dens.
INVENTED — gap_id/owner fields; ledger holds no rows for this asset ("rendered, never retyped"
unsatisfiable). Clause: tier-4 §5 "rendered, never retyped".

## §6 · Change packet — NOT AUTHORED (test artefact). The fix direction the census implies is registry-
or code-side (register a writer or correct has_writer) — permitted: "Fixes go in the asset or the
registry — never in the orchestrator."

## §9 · Opportunities — one candidate: a service health signal so rows_written=0 stops being ambiguous
(pilot 4's O-row). Not admitted: no measurement-after specifiable from census alone.

## §7 · Certification — none (pilot).  ## §8 · Review — unsigned. **Derivability: 1 of 13 clean (row 2),
3 partial (1, 9, 10), 9 invented (3, 4, 5, 6, 7, 8, 11, 12, 13). The service kind is the heaviest
invention load of the two briefs — the template's §1 storage bullets, Vocab gate, contract row shape and
ablation flavour all presume a table.**
