# TEST ARTEFACT — NOT AN ASSET BRIEF (pilot: yes)

ga_prashna — derived from tier-4 template v2.0 + `L1_INSTANCE_SKELETON.md` (TEST) + tiers 1–2 +
census `L1_prod_20260926.json`. **Edge kind: empty** — target table `ga_prashna_judgment` has zero
rows, zero serving modules, `rows_written=0` against `state='lit'`. Invention ids continue the L1
series.

## §0 · Identity and inheritance

```
inherits:    layer skeleton §4.4; Data plane §13.3; Product §16
measured_by: none — definitional
traces_to:   layer §0.1
```

```
asset_id: ga_prashna · layer: L1 Gaṇita · pilot: yes
kind: data (writer-backed, single target table, EMPTY) · scoring_mode: contribution · role: neither
layer_instance: nikasha_test/derivations/L1_INSTANCE_SKELETON.md (TEST ARTEFACT)
measured_on: 2026-09-26
measured_against: census L1_prod_20260926.json
```

### 0.1 · Inherited — thirteen rows

| # | what | value | derivable? |
|---|---|---|---|
| 1 | P/V served | INVENTED — praśna computation serves the praśna P-need; ids not named per asset by any tier | NO — INV-L1-01 chain |
| 2 | obligations | Computational correctness (Product §11 L1 row) | YES |
| 3 | correctness rules + switch | §8.1 L1 row verbatim; switch behaviour INVENTED (INV-L1-04) | PARTIAL |
| 4 | presentation fields | conventions + intermediate quantities via DP03 (INV-L1-05) | PARTIAL |
| 5 | contracts | produces DP03 facts (praśna judgments); consumes DP01/DP02 — declared use: calculation identity, applicability | YES at contract level |
| 6 | coverage owned + state | praśna computation; state **unqualified** (census width NOT_GENERIC); content state **unavailable** — table empty | PARTIAL (INV-L1-06) |
| 7 | position + baseline | DAG: 2 edges, resolvable; exercised 51 runs; deployed **0 rows**; current-code vs deployed NOT_MEASURED (INV-L1-03) | PARTIAL |
| 8 | disposition + must-add | INVENTED — **U (unresolved use)**: writer exercised 51 times, zero rows ever produced, zero serving modules. Must-add: none derivable. (Alternative readings H or R cannot be distinguished without the missing 0.1 row.) | NO — INV-L1-10 |
| 9 | individual term | ≈ 0 — "An asset that cannot be ablated because nothing reads it has already answered the question" (tier 3 §1.2): 0 modules read it | YES — template rule applies directly |
| 10 | synergistic term | NOT MEASURED — no harness | absent instrument |
| 11 | cross-layer term | none reached — evidence state: source-present only | YES (from census Dens N/A: 0 modules) |
| 12 | preserved kernel | INVENTED — the praśna judgment algorithm in ga_prashna.py; the table schema; (no rows to preserve) | NO — INV-L1-10 |
| 13 | concepts + carriage check | INVENTED — concept: praśna (horary) judgment computation; check **D3** per tier-4 L1 row | NO — INV-L1-08 (C-9) |

### 0.2 · What this asset is for

Computes praśna (horary) judgments into `ga_prashna_judgment`. Today it computes nothing: 51
orchestrator runs, zero rows, zero serving modules. Per tier 4 §0.2: "If the paragraph cannot be
written, the disposition is in question and §5 says so" — the paragraph above is the best the
documents support; the disposition is in question (row 8).

## §1 · Measured current state

```
measured_by: census L1_prod_20260926.json, asset ga_prashna (population: ga_prashna_judgment, production, 2026-09-26)
```

- **Storage:** `ga_prashna_judgment` — **0 rows** ("table empty", depth PASS-vacuous); key
  (chart_id, ayanamsha_id), 0 duplicates.
- **Producer:** `ga_prashna.py`, `@register` present, contract conformant, target declared.
- **Consumers:** 2 DAG edges in (resolvable); **0 capability modules** serve it; 0
  density_contracts.
- **Three-way baseline:** deployed 0 rows · current code NOT_MEASURED · target: this brief.
- **Build cost:** FAIL-to-record — `state=lit, rows_written=0, rps=-`: **for an empty asset,
  rows_written=0 is indistinguishable from a healthy no-op** — and for a service, tier 4 §4.2
  check 6 already names this confusion ("for a service it is indistinguishable from a writer that
  produced nothing"). For a *data* asset with a declared target, the documents give no
  "empty-by-design" verdict.

**INVENTED — the distinction between "empty by design", "writer ran and produced nothing", and
"writer never effective", for a data asset, clause that should have provided it: "**completion
honesty** | the build record agrees with the live count. `rows_written = 0` against a populated
table is a status with no measurement behind it, and for a service it is indistinguishable from a
writer that produced nothing" (tier 4 §4.2, check 6). The clause covers populated tables and
services; an empty data table with state=lit is the third case and is not covered.** — INV-L1-17.

- **History:** latest complete; 0 errors / 7 aborts.

### 1.1 · Concept completeness

`Complete.width: NOT_GENERIC` — no declared universe (same defect as INV-L1-16's clause: "Declare
the universe first, from a source or from the ontology", tier 4 §1.1). For praśna the universe is
unstated in every document read. INVENTED if supplied; recorded as gap G-P4 instead.

### 1.2 · Retrieval reachability

0 modules expose it; there is nothing to reach. [TRANSFERS] to the retrieval plane — recorded as
opportunity only (tier 4 §1.2), the mechanical case.

## §3 · Obligations specialised

| obligation | satisfied means for ga_prashna | detector |
|---|---|---|
| Computational correctness | a praśna judgment reproduces a second way, within tolerance — **vacuous while the table is empty** | D3 — does not exist; cannot run on 0 rows |

## §4 · The nine gates (evaluated from census)

| gate | verdict | evidence |
|---|---|---|
| Ldgr | N/A | 0 rows — nothing to carry a citation_ref; N/A with reason, per the closed-set rule |
| Idem | PARTIAL | no idempotency pattern in writer SQL; delegates |
| Earn | FAIL | rows_per_second NULL; state=lit over 0 rows (INV-L1-17) |
| Null | NOT_MEASURED | no probe |
| Vocab | PASS | key (chart_id, ayanamsha_id), 0 duplicates |
| Carr | NO_DETECTOR | D3 applicable per tier-4 L1 row; none exists; cannot run empty |
| Narr | N/A | no prose |
| Dens | N/A | 0 modules, 0 density_contracts — never reaches a served surface |
| Build | PARTIAL | checks 1–5 PASS; completion N/A per census; history PARTIAL (7 aborts); exercised PASS (51 runs) — the asset is dispatched and completes without effect |

## §5 · Ledger rows

- `ga_prashna · G-P1 · gap · Build.completion/Earn · measured: state=lit, rows_written=0, 0 live rows (census) / required: "the build record agrees with the live count" · detector: row-count vs build-record join · gate: Build · state OPEN`
- `ga_prashna · G-P2 · gap · Carr · measured: NO_DETECTOR / required: reproduces a second way · detector: D3 (to be built; blocked by empty content) · gate: Carr · state OPEN`
- `ga_prashna · G-P3 · gap · Idem · measured: no pattern in writer SQL / required: delete-then-insert on chart × natural key · detector: SQL pattern at delegated site · gate: Idem · state OPEN`
- `ga_prashna · G-P4 · gap · width · measured: NOT_GENERIC / required: five-state census against a declared universe · detector: census once universe declared · gate: none — layer packet · state OPEN`
- `ga_prashna · G-P5 · gap · disposition-evidence · measured: 51 runs, 0 rows, 0 modules / required: a disposition decision needs the served-necessity chain (row 1) · detector: none — question raised against the layer instance per tier 4 §5 ("A gap with no detector is not registered; it is written as a question and raised against the layer instance") · state OPEN`

## §9 · Opportunity register

| dimension | entry | proof afterward |
|---|---|---|
| synergy | none proposed — an asset with zero output has no measurable joint distinction (tier 4 §9 synergy guardrail applies by vacuity) | — |
| reachability [TRANSFERS] | moot until content exists | — |

## §6 · Change packet — not authorised (pilot)

```
may_touch:      platform/python-sidecar/**/ga_prashna.py
must_not_touch: pipeline/orchestrator/** · applied migrations
base:           campaign/nikasha-test HEAD
```

Preserved kernel: per row 12 (INVENTED). First question, before any delta: **is this asset
supposed to produce rows?** — that is a layer-instance question (§0.1 necessity), not an asset
question, and it is currently unanswerable from the documents (INV-L1-01).

## §2 · Shape

identity ✓ inputs/DAG ✓ correctness ✓ data sufficiency ✓ (empty, honestly) consumers ✓ (none,
honestly) value/target ✓ synergy ✓ knowledge-time ✓ change packet ✓ evidence ✓

## §7 · Certification — none (pilot)

## §8 · Review — unsigned. Derivability: **4 of 13 rows clean** (2, 5, 9, 11 — rows 9 and 11 clean
precisely because the template's "record ≈ 0" and the census's 0-module reading answer them
without invention); rows 1, 8, 12, 13 invented; 3, 4, 6, 7 partial; 10 absent instrument.
**C-9 confirmed a fifth surface.** Edge-kind note: the template handles "empty" only negatively
(≈ 0 contribution, disposition U); nothing tells a reader whether an empty writer-backed asset in
a contribution layer is a defect or a design state — that question routes back to the missing
layer-level necessity set (INV-L1-01) and is this layer's sharpest instance of it.
