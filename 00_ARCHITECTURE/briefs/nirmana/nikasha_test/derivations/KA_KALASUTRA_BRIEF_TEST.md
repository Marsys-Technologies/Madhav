---
artifact: KA_KALASUTRA_BRIEF_TEST
canonical_id: KA_KALASUTRA_BRIEF_TEST
status: TEST ARTEFACT — NOT A BRIEF
pilot: yes
campaign: nikasha-test, Phase 4
produced_on: 2026-09-26
template: 00_ARCHITECTURE/briefs/nirmana/ASSET_ELEVATION_TEMPLATE_v2_0.md
layer_instance: 00_ARCHITECTURE/briefs/nirmana/nikasha_test/derivations/L3_INSTANCE_SKELETON.md (TEST ARTEFACT — NOT AN INSTANCE)
measured_against: "census L3_sandbox_20260926.json — SANDBOX RUN, not production"
verdict: NONE
---

# ka_kalasutra — asset brief TEST ARTEFACT (pilot: yes)

Ordinary writer-backed asset. Census (sandbox): writer `ka_kalasutra.py` (@register PASS), target
`kala_activation`, 16,925 rows / 15 cols, source_citation 100%, 5 DAG edges all resolvable,
dep_liveness FAIL (ka_sangam not lit), Dens.served FAIL (3 modules, 0 density_contracts), history
PARTIAL (33 errors / 13 aborts on record, latest complete).

## §0 · Identity and inheritance

```
asset_id: ka_kalasutra · layer: L3 Kāla · pilot: yes
kind: data · scoring_mode: contribution · role: temporal
measured_on: 2026-09-26 (sandbox census)
```

### 0.1 · Inherited — thirteen rows (invention record; §8-style)

| # | value | filled from | invented? |
|---|---|---|---|
| 1 P/V | P24 / V13 only | tier2 DP08 (present+preceding interval) | NO for P24/V13; **INVENTED** — any wider P/V set. Clause: layer template §0.1 "List the P-needs and V-journeys for which this layer is **necessary**" (no per-layer P/V mapping exists in tiers 1–2) |
| 2 obligations | Temporal integrity | Product §11 L3 row | NO |
| 3 correctness + switch | "Using the observed event to choose the supposedly prior trigger" (verbatim) | Product §8.1 L3 row | NO for the rule; **INVENTED** — switch ON/OFF behaviour for this asset and its detector. Clause: layer §2.1 "The life-event switch: what this layer may do when ON, what it emits when OFF, and the storage separation…" |
| 4 presentation fields | clock geometry, activation rule, named criterion, bridge/falsifier | layer template §2.2 temporal row | **INVENTED** — the mapping of those field names to this asset's actual columns. Clause: data plane §13.3 item 6 "which §3.4 presentation rows this layer carries and which fields it hands onward for them" |
| 5 contracts | consumes DP05/DP06/DP07; produces DP08 (as one L3 integrator) | tier2 §7.1 | **INVENTED** — that ka_kalasutra specifically (not the layer) produces DP08's mechanism rows, plus fields/grain/declared use. Clause: layer §2.3 "for each contract, the fields and grain actually present in the producer's table and actually read by the consumer — verified both ends" |
| 6 coverage | Kāla activation (daśā/gochara contact) | Product §3 instrument list | **INVENTED** — the five-state verdict per obligation. Clause: layer §2.4 "applied / inapplicable-with-reason / unavailable / unqualified / unresolved — the five states, never a blank" (no instrument exists; census Complete.width = NOT_GENERIC) |
| 7 position + baseline | 3 DAG edges resolvable; 115 runs, scopes asset/asset_set/global/layer | census Build.dag / Build.exercised | **INVENTED** — topological position and three-way baseline (deployed/current-code/target). Clause: layer §4.1 "State the three-way baseline per asset: deployed … current code … target" (census reads no current code; sandbox is not deployed production) |
| 8 disposition + must-add | E — enrich (dep_liveness FAIL on ka_sangam; Dens FAIL) | reader judgement on census | **INVENTED** — disposition and must-add list. Clause: layer §3.2 "one of the data plane's eight dispositions, with the evidence from Part 1 that justifies it" (the skeleton's Part 3 was never derivable, so nothing inherits) |
| 9 individual term | NOT MEASURED — no ablation harness | layer §1.2 permission | NO (honest null permitted by template) |
| 10 synergistic term | sits on the convergence seam with ka_sangam / ka_vighnakara | inferred from dep graph | **INVENTED** — seam membership; only "recorded seam-by-seam" is permitted sans harness, and no seam list exists for L3. Clause: layer §1.3 `inherits:` "the layer's synergy binding if one exists" — none exists |
| 11 cross-layer term | DP08 producer; evidence state at consumer unverified | tier2 §7.1 | **INVENTED** — the evidence state "verified at the consumer". Clause: layer §1.4 `measured_by:` "verified at the consumer, not asserted by the producer" (no consumer-side read was run) |
| 12 preserved kernel | the kala_activation rows' natural grain and source_citation column | reader judgement | **INVENTED** — the kernel itself. Clause: layer §4.4 "**the preserved kernel** — what of the asset must survive any rebuild unchanged (from 3.2)" (§3.2 never derived) |
| 13 concepts + carriage check | daśā/activation concept → reader chose **D3** (activation intervals computable a second way); D1 N/A, D2 N/A | CHOSEN BY AUTHOR | **INVENTED — C-9/R09 CONFIRMED (5th confirmation).** Clause: layer §4.4 "**the relevant Jyotish concepts** the asset touches, named, with the domain detector each invites (2.7, 5.2's menu)" — census `Carr.detector: NO_DETECTOR` for all 23 L3 assets; no tier assigns the check per asset |

### 0.2 · What it is for
INVENTED prose (no tier provides it): the activation engine — the table that says which daśā/transit
contacts are live for a chart in which interval. Removing it leaves L3 with clocks but no engagements.

## §1 · Measured current state (sandbox census only)

- Storage: `kala_activation`, 16,925 rows, 15 cols, 10 fully populated (Complete.depth PASS).
- Producer: `ka_kalasutra.py`, @register + registry agree; Idem PASS (delete-then-insert).
- Consumers: declared 5 edges in; actual readers not grep-measured. INVENTED — actual-consumer census.
  Clause: tier-4 §1 "code that actually reads it, writer-side and serving-side, grep population stated".
- Served: 3 modules (call_service_wrappers.ts, index.ts, query_temporal_activation.ts); 0 density_contracts.
- Baseline: deployed = sandbox proxy only; current code not read. INVENTED — see row 7.
- Build cost: `Cost.baseline FAIL` — state=stale, rows_written=335,403, rps=NULL. "not instrumented".
- Evidence state: source-present ✓ (100% citations); consumed..served NOT VERIFIED at consumer.

### 1.1 / §1.2 completeness & reachability
Complete.width = NOT_GENERIC ("no declared universe"). INVENTED — the declared universe (which
daśā systems × contact kinds should exist). Clause: tier-4 §1.1 "Declare the universe first, from a
source or from the ontology". Reach.fields = NOT_GENERIC. [TRANSFERS] noted per tier-4 §1.2.

## §2 · Shape — markers present: identity ✓ inputs/DAG ✓ correctness ✓ data sufficiency ✓ consumers ✓ value/target ✓ synergy ✓ knowledge-time ✓ change packet ✓ evidence ✓ (self-scan, no records)

## §3 · Obligations specialised
INVENTED — "what satisfied means" rows. Clause: tier-4 §3 "what satisfied means for this asset
specifically" is authored content; the template correctly leaves it to the brief, so NOT counted as an
invention against the tiers — recorded here as authored, not derived.

## §4 · Nine gates (from census; verdicts are sandbox verdicts)

| gate | verdict | evidence (census) |
|---|---|---|
| Ldgr | PASS | source_citation 16,925/16,925 |
| Idem | PASS | delete-then-insert in writer |
| Earn | FAIL | rows_per_second=NULL |
| Null | NOT MEASURED | census has no Null check — INVENTED: no verdict possible. Clause: tier-4 §4 "**Null** … an underivable value is emitted as null" — the inspector runs no such check |
| Vocab | PASS (identity half only) | declared key (id): 0 duplicates; alias-set conformance not measured |
| Carr | NO_DETECTOR | D3 chosen by author (C-9); no detector exists |
| Narr | N/A | emits no prose (author judgement from target shape) |
| Dens | FAIL | 3 modules, 0 density_contracts |
| Build | PARTIAL | registered/contract/target/dag/count_integrity PASS; dep_liveness FAIL (ka_sangam); completion N/A; history PARTIAL |

## §5 · Delta ledger — rows implied by census FAILs: Earn.build_record, Cost.baseline, Dens.served,
Build.dep_liveness (ka_sangam). INVENTED — gap_id/owner/packet fields. Clause: tier-4 §5 "This section
is those rows for this asset, in the ledger's own fields … rendered, never retyped" — the ledger holds
no rows for ka_kalasutra today, so "rendered, never retyped" cannot be satisfied; the rows would be
authored here.

## §6 · Change packet — NOT AUTHORED (test artefact). INVENTED if attempted: may_touch/must_not_touch
globs. Clause: tier-4 §6 "may_touch: <exact globs>" — no tier or census supplies these.

## §9 · Opportunities — none admitted (no measurement-after could be specified from census alone).

## §7 · Certification — none (pilot).  ## §8 · Review — unsigned. **Derivability: 2 of 13 rows clean
(2, 9), 4 partial (1, 3, 4, 5), 7 invented (6, 7, 8, 10, 11, 12, 13).**
