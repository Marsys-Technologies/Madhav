---
artifact: PH_MUHURTA_BRIEF_TEST
canonical_id: PH_MUHURTA_BRIEF_TEST
tier: 4
kind: instance
version: "0.1-test"
status: TEST ARTEFACT — pilot derivation, campaign nikasha-test Phase 4
template: 00_ARCHITECTURE/briefs/nirmana/ASSET_ELEVATION_TEMPLATE_v2_0.md
layer_instance: TEST ARTEFACT — L4_INSTANCE_SKELETON.md (not ACCEPTED; hence pilot)
pilot: yes
measured_on: 2026-09-26
measured_against: "census L4_prod_20260926.json (production read-only proxy); L4_sandbox_20260926.json (identical verdicts)"
verdict: NONE
---

# ph_muhurta — asset brief (TEST ARTEFACT, pilot)

Ordinary writer-backed L4 asset, chosen per campaign Phase 4 (one ordinary + one edge kind).

## §0 · Identity and inheritance

```
asset_id: ph_muhurta · layer: L4 Phala · pilot: yes
kind: data (writer-backed) · scoring_mode: contribution · role: manifestation
measured_on: 2026-09-26
```

role: manifestation — INVENTED. Clause: tier-4 §0 `role: manifestation | temporal | neither
(supplies what both rest on)   # from layer §4.4` — the layer skeleton's §4.4 has no
per-asset role row; the template cites "layer §4.4" but §4.4's thirteen rows contain no
role row. ("manifestation" guessed from the tier-2 §3.1 L4 row "Qualified manifestation
alternatives".)

### 0.1 · Inherited — thirteen rows

| # | what | value | source / invention |
|---|---|---|---|
| 1 | P/V served | INVENTED — no per-layer P/V map exists (skeleton 0.1) | clause: tier-3 0.1 `inherits: Product §2 (P01-P24), Data plane §2 (V01-V13)` |
| 2 | obligations scored on | Interpretive fidelity + Distinctive understanding (layer subset) | tier-1 §11 L4 row — DERIVED |
| 3 | correctness rules + switch | "must not rewrite the original forecast"; switch behaviour INVENTED (no L4 switch clause in any parent) | tier-1 §8.1; clause missing: tier-3 2.1 "The life-event switch: what this layer may do when ON, what it emits when OFF" — stated generically, never per layer |
| 4 | presentation fields | INVENTED — selected the manifestation-bridge/falsifier fields by judgement | tier-2 §13.3 item 6 requires the layer plan to state the rows; no assignment exists |
| 5 | contracts | consumes DP03/DP04/DP05/DP08/DP09 (inferred from §7.1 producer→consumer columns); declared uses INVENTED | tier-3 2.3 "Every consumed input declares its use" — no parent declares them |
| 6 | coverage obligations | INVENTED; census: Complete.width NOT_GENERIC ("no declared universe for this asset") | tier-3 2.4; no per-layer coverage assignment |
| 7 | position + baseline | DERIVED (census): after ph_nimitta (dependency); deployed = 183 rows in phala_muhurta, build state `stale`, last build 2026-08-12/13, 99 runs (scopes asset_set/global/layer); current-code leg NOT MEASURED — no instrument | tier-3 §4.1 "current code (newest on any live head, including unmerged)" — no instrument named |
| 8 | disposition + must-add | INVENTED — skeleton 3.2/3.3 could not be derived (ablation harness absent) | tier-3 3.2 requires Part 1 evidence that requires ablation |
| 9 | individual term | BLOCKED, not invented — no ablation harness (tier-3 1.2; "record ≈ 0" only where a search ran) | tier-3 1.2 `measured_by: ablation of the single asset against the layer's served reading` |
| 10 | synergistic term | BLOCKED — seam-by-seam only: it reads ph_nimitta + 4 ka_* assets (census edges) | tier-3 1.3/1.5 |
| 11 | cross-layer term | PARTIAL — serves 3 capability modules (index.ts, query_phala_calibration.ts, salience_order.ts), 0 density_contract declarations; consumer-verified six-state position NOT MEASURED | tier-3 1.4 `measured_by: ... verified at the consumer` |
| 12 | preserved kernel | INVENTED — would say: the 183 rows, muhurta_id identity, source_citation column, delete-then-insert pattern | tier-3 §4.4 "the preserved kernel ... (from 3.2)" — 3.2 underivable |
| 13 | concepts + carriage check | INVENTED — concepts: muhūrta (electional timing); carriage check chosen here: **a (source correspondence)** — the asset restates classical electional rules (source_citation on 183/183 rows). **C-9/R09 confirmed, fifth occurrence.** | tier-3 §2.7 "For each obligation the layer owns (§2.4), state which of a–c applies" — layer scope only |

### 0.2 · What this asset is for

DERIVABLE from census + tier-2 §3.1 without further invention: ph_muhurta computes electional
(muhūrta) propositions into `phala_muhurta` (183 rows, 24 cols) from the L3 temporal
substrate and ph_nimitta anchors; removing it removes the layer's electional-outcome surface.

## §1 · Measured current state (from census, production 2026-09-26)

- Storage: `phala_muhurta`, 183 rows / 24 cols, 21 fully populated, none never-populated;
  count_sql and integrity_check_sql present (Build.count_integrity PASS).
- Producer: `@register` in ph_muhurta.py; registry agrees (Build.registered PASS);
  contract conformant (Build.contract PASS); Idem: delete-then-insert (Idem.pattern PASS).
- Consumers: 8 declared edges, all resolvable; served by 3 capability modules, 0 declaring
  density_contract (Dens.served FAIL).
- Baseline: deployed rows 183; build state `stale`, last_built 2026-08-12, 99 recorded runs;
  rows_written=56 in latest record vs 183 live rows (Cost.baseline FAIL; Earn.build_record
  FAIL, rows_per_second NULL). Build cost: not instrumented — census's legal value.
- Build.completion N/A reads "no count_sql" while count_integrity PASS reads "count_sql=yes"
  — inspector internal contradiction (recorded in skeleton 1.1).
- dep_liveness FAIL: declared dependencies not lit — ph_nimitta, ka_kalasutra,
  ka_vighnakara, ka_sangam.

### 1.1 · Completeness — NOT MEASURABLE: Complete.width NOT_GENERIC, no declared universe.
### 1.2 · Reachability — NOT MEASURED: Reach.fields NOT_GENERIC (per-capability census not run). Requirement [TRANSFERS].

## §3 · Obligations specialised — INVENTED where filled; the layer subset (row 2) gives
only two obligations; what "interpretive fidelity" means for an electional table
specifically has no parent text. Clause: tier-4 §3 "An obligation inherited but not
specialised is an obligation nobody can test." — the demand exists; the content to
specialise *from* does not.

## §4 · Gates (verdicts from census, not re-run)

Ldgr PASS (source_citation 183/183) · Idem PASS · Earn FAIL (build record) · Null — not in
census vocabulary; INVENTED mapping needed: census emits no Null-gate reading; clause:
tier-4 §4 gate table lists **Null** as "always" — the inspector runs no such check, so the
brief cannot fill it from the census · Vocab PASS (0 dup on muhurta_id) · Carr NO_DETECTOR ·
Narr — not in census; the asset emits no prose by inspection of the table profile —
INVENTED · Dens FAIL · Build PARTIAL/FAIL composite (history PARTIAL 29 err/10 abort;
dep_liveness FAIL; exercised PASS).

## §5 · Ledger rows — would register: Earn.build_record FAIL; Cost.baseline FAIL (stale);
Dens.served FAIL ×3 modules; Build.dep_liveness FAIL (4 unlit deps); Complete.width
NOT_GENERIC (universe undeclared); Carr NO_DETECTOR. Rendered here, not written (test).
INVENTED — gap_id namespace and owner values; clause: tier-4 §5 "`asset · gap_id · kind ·
criterion · what · change · detector · owner · gate · state · ts`" — the `_schema` line is
declared the authority but was not consulted for this test fill.

## §9 · Opportunities — none recorded (test fill stops at §5).

## §2 · Shape — identity ✓ inputs/DAG ✓ correctness ✓ data sufficiency ✓ consumers ✓
value/target ✓ synergy ✓ knowledge-time ✓ change packet ✓ evidence ✓ (present as sections).

## §7 · Certification — none (pilot).
## §8 · Review — unsigned. **Derivability: 4 of 13 rows clean (2, 7-partial, 10-partial, 11-partial); rows 1, 3(switch), 4, 5(uses), 6, 8, 12, 13 invented; rows 9, 10 blocked by absent harness. Row 13 chosen by the brief author — C-9 confirmed.**
