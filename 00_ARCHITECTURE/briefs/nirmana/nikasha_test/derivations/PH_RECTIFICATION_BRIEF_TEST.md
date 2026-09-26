---
artifact: PH_RECTIFICATION_BRIEF_TEST
canonical_id: PH_RECTIFICATION_BRIEF_TEST
tier: 4
kind: instance
version: "0.1-test"
status: TEST ARTEFACT — pilot derivation, campaign nikasha-test Phase 4
template: 00_ARCHITECTURE/briefs/nirmana/ASSET_ELEVATION_TEMPLATE_v2_0.md
layer_instance: TEST ARTEFACT — L4_INSTANCE_SKELETON.md (not ACCEPTED; hence pilot)
pilot: yes
measured_on: 2026-09-26
measured_against: "census L4_prod_20260926.json; grep over platform/python-sidecar/pipeline/orchestrator/writers/** at branch head campaign/nikasha-test"
verdict: NONE
---

# ph_rectification — asset brief (TEST ARTEFACT, pilot)

Edge-kind asset: **registry declares `has_writer=true` but the census finds no writer file**
(`Build.registered` FAIL: "registry says has_writer=true and no @register found"). The truth,
by independent grep: `writers/ph_rectification/__init__.py:246` contains
`@register("ph_rectification")` — the writer exists **as a package**, and the inspector's
registered check does not look inside `__init__.py`. A three-source disagreement (registry
true / code true / inspector false) and the reason `registered_ids` (8) ≠
`registry_has_writer` (9) for L4. Whether the orchestrator can actually dispatch a
package-shaped writer is NOT MEASURED here.

## §0 · Identity and inheritance

```
asset_id: ph_rectification · layer: L4 Phala · pilot: yes
kind: data (writer-backed, writer packaged) · scoring_mode: contribution · role: manifestation
```

kind: INVENTED. Clause: tier-4 §0 `kind: data | service (no table by design) | multi-table
| rider (producer_covered) | static (migration-seeded)` — the closed list has **no value for
"writer exists but the inspector cannot see it"**; the census's own kinds do not cover the
package-writer case. `data` chosen as least-wrong.
role: INVENTED (same gap as ph_muhurta — no §4.4 role row).

### 0.1 · Inherited — thirteen rows

| # | what | value | source / invention |
|---|---|---|---|
| 1 | P/V served | INVENTED (skeleton 0.1; no per-layer P/V map) | tier-3 0.1 inherits line |
| 2 | obligations | Interpretive fidelity + Distinctive understanding | tier-1 §11 — DERIVED |
| 3 | correctness + switch | "must not rewrite the original forecast" DERIVED (and doubly apt for a rectification asset — tier-1 §8.1's L4 row); switch behaviour INVENTED | tier-3 2.1 has no per-layer switch clause |
| 4 | presentation fields | INVENTED | tier-2 §13.3 item 6 — assignment absent |
| 5 | contracts | consumes DP03/DP09-family (inferred); declared uses INVENTED; 1 declared edge, resolvable (census) | tier-3 2.3 |
| 6 | coverage obligations | INVENTED; Complete.width NOT_GENERIC | tier-3 2.4 |
| 7 | position + baseline | PARTIAL (census): target `phala_rectification`; build state `stale`; exercised/history PARTIAL; current-code leg NOT MEASURED | tier-3 §4.1 instrument gap |
| 8 | disposition + must-add | INVENTED (ablation harness absent) | tier-3 3.2 |
| 9 | individual term | BLOCKED — no harness; additionally the asset's readability is unknown because its writer is invisible to the inspector | tier-3 1.2 |
| 10 | synergistic term | BLOCKED | tier-3 1.3/1.5 |
| 11 | cross-layer term | PARTIAL — Dens.served FAIL (serving modules, 0 density_contract) | tier-3 1.4 |
| 12 | preserved kernel | INVENTED | tier-3 §4.4 "(from 3.2)" — 3.2 underivable |
| 13 | concepts + carriage check | INVENTED — concept: birth-time rectification; check chosen: **a (source correspondence)** on the restated rectification rules. **C-9/R09 confirmed, sixth occurrence.** | tier-3 §2.7 per-obligation scope only |

### 0.2 · What this asset is for

Rectification support: `phala_rectification` holds the layer's birth-time-rectification
propositions. Without it no L4 output can speak to uncertain birth time. (Content sentence
DERIVABLE from the asset id + tier-1 §13's "no automatic rectification" boundary; the
table-level claim is census-only.)

## §1 · Measured current state (census + grep)

- Storage: `phala_rectification`; count_sql and integrity_check_sql present
  (Build.count_integrity PASS); row count not reported by census for this asset.
- Producer: registry has_writer=true; census writer_files=[]; **truth**:
  `writers/ph_rectification/__init__.py` with `@register("ph_rectification")` at L246.
  Build.contract N/A and Idem.pattern N/A ("no writer file") are **inspector artefacts**, not
  asset facts.
- Consumers: 1 declared edge, resolvable (Build.dag PASS).
- Baseline: build state `stale`; Cost.baseline FAIL; Earn.build_record FAIL.
- dep_liveness FAIL (as all L4 assets — unlit declared dependencies).

## §3 · Obligations specialised — INVENTED where filled (same gap as ph_muhurta brief §3).

## §4 · Gates (census verdicts; two marked as inspector artefacts)

Ldgr — not reported separately · Idem N/A (artefact — writer is packaged) · Earn FAIL ·
Null — no census check exists; INVENTED (tier-4 §4 lists Null "always"; inspector has no
such check) · Vocab — not reported for this asset · Carr NO_DETECTOR · Narr — INVENTED
N/A-by-inspection · Dens FAIL · **Build FAIL (registered) — FALSE POSITIVE**; dag PASS;
history PARTIAL; dep_liveness FAIL.

## §5 · Ledger rows — would register: the three-source disagreement on the writer (system
finding, inspector scope), dep_liveness FAIL, Earn/Cost FAIL, Carr NO_DETECTOR,
width NOT_GENERIC. INVENTED — gap_id namespace/owner (same clause as ph_muhurta §5).

## §9 / §2 — none / shape present (test fill).
## §7 · Certification — none (pilot).
## §8 · Review — unsigned. **Derivability: rows 2, 5-partial, 7-partial, 11-partial clean; 1, 3(switch), 4, 6, 8, 12, 13 invented; 9, 10 harness-blocked. Row 13 chosen by author — C-9 confirmed. Edge-kind lesson: the tier-4 `kind` vocabulary cannot express "packaged writer the inspector missed".**
