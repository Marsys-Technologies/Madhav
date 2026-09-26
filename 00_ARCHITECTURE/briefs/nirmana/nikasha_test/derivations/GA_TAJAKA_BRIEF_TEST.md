# TEST ARTEFACT — NOT AN ASSET BRIEF (pilot: yes)

ga_tajaka — derived from tier-4 template v2.0 + `L1_INSTANCE_SKELETON.md` (TEST) + tiers 1–2 +
census `L1_prod_20260926.json`. Ordinary writer-backed asset. Every invention against the thirteen
§0.1 rows is in §8. Invention ids continue the L1 series (INV-L1-nn).

## §0 · Identity and inheritance

```
inherits:    layer skeleton §4.4 (thirteen items); Data plane §13.3; Product §16
measured_by: none — definitional
traces_to:   layer §0.1
```

```
asset_id: ga_tajaka · layer: L1 Gaṇita · pilot: yes (layer instance not ACCEPTED — it is a test skeleton)
kind: data (writer-backed, single target table) · scoring_mode: contribution · role: temporal (Tājaka varṣa)
layer_instance: nikasha_test/derivations/L1_INSTANCE_SKELETON.md (TEST ARTEFACT)
measured_on: 2026-09-26
measured_against: census L1_prod_20260926.json (live registry · build_runs · production counts)
```

### 0.1 · Inherited — thirteen rows

| # | what | value | from | derivable? |
|---|---|---|---|---|
| 1 | P/V served | INVENTED — V-journey(s) consuming varṣaphala year-lord facts; specific P/V ids not named by any tier for this asset | layer §0.1 narrowed | NO — INV-L1-01 chain |
| 2 | obligations scored on | Computational correctness (L1's row of the ten) | Product §11 | YES |
| 3 | correctness rules + switch | "L1 must not alter birth facts to fit biography" (Product §8.1); switch: computes identically both states (INVENTED, INV-L1-04) | layer §2.1 | PARTIAL |
| 4 | presentation fields | conventions in force; intermediate quantities (via DP03) | layer §2.2 (itself INV-L1-05) | PARTIAL |
| 5 | contracts produced/consumed | produces DP07-clock primitives (varṣa year-lord intervals) / DP03 facts; consumes DP01, DP02 (declared use: calculation identity, applicability) | Data plane §7.1 | YES at contract level |
| 6 | coverage owned + state | Tājaka varṣa (year-lord) computation; state **unqualified** — census `Complete.width: NOT_GENERIC` | census | PARTIAL (obligation list INV-L1-06) |
| 7 | position + baseline | DAG: 3 edges, resolvable; build order after ga_dashas (run history: blocked on ga_dashas); deployed 780 rows; current-code vs deployed NOT_MEASURED (INV-L1-03) | census | PARTIAL |
| 8 | disposition + must-add | INVENTED — **P** (preserve): depth PASS, served, exercised 67 runs; must-add: none derivable | census evidence; no tier maps evidence → disposition | NO — INV-L1-10 |
| 9 | individual term | NOT MEASURED — no ablation harness; absent instrument | tier 3 §1.2 | NO (absent instrument) |
| 10 | synergistic term | NOT MEASURED — harness absent | tier 3 §1.3/§1.5 | NO (absent instrument) |
| 11 | cross-layer term | DP07/DP03 producer; evidence state: served (2 modules: coverage_matrix.ts, get_tajik.ts; 1 declaring density_contract); value-evaluated NOT_MEASURED | census Dens.served | PARTIAL |
| 12 | preserved kernel | INVENTED — the 780 rows of `l1_tajik_varsha_year_lords`; key (chart_id, ayanamsha_id, build_id, varsha_year); the year-lord algorithm in ga_tajaka.py | no tier states it | NO — INV-L1-10 |
| 13 | Jyotish concepts + carriage check | INVENTED — concept: Tājaka varṣa / munthā year-lord determination; carriage check **D3** (re-derivation), per tier-4 L1 row "Carr D3 dominates" | tier 4 L1 row gives the check class only; the named concept per asset is unstated | NO — INV-L1-08 (C-9 confirmed) |

### 0.2 · What this asset is for

Computes the Tājaka annual (varṣaphala) year-lord assignments per chart per year — the L1 clock
primitive that L3's Tājaka engagement reads. Without it, every year-lord question recomputes the
varṣa chain downstream, which Product §11 forbids. (Paragraph written from tier-2 §3.1's L1 row
plus the census; the Tājaka-specific necessity is INVENTED per row 1.)

## §1 · Measured current state

```
inherits:    layer §1.1, §4.1
measured_by: census L1_prod_20260926.json, asset ga_tajaka (population: l1_tajik_varsha_year_lords, production, 2026-09-26)
traces_to:   layer §0.3
```

- **Storage:** `l1_tajik_varsha_year_lords` — 780 rows, 18 columns, all 18 populated (depth PASS);
  key (chart_id, ayanamsha_id, build_id, varsha_year), 0 duplicates.
- **Producer:** `ga_tajaka.py`, `@register` present, registry agrees (Build.registered PASS);
  contract conformant.
- **Consumers:** 3 DAG edges in, resolvable; served by 2 capability modules
  (coverage_matrix.ts, get_tajik.ts), 1 with density_contract. Declared-vs-actual reader gap
  NOT_MEASURED (census is module-level, not reader-level).
- **Three-way baseline:** deployed 780 rows · current code NOT_MEASURED (INV-L1-03) · target: this
  brief. Delta and risk uncomputable as specified.
- **Evidence state:** source-present ✓ qualified ✓ consumed ✓ served ✓ · transformed /
  value-evaluated NOT_MEASURED at the consumer.
- **Build cost:** FAIL-to-record — `rows_per_second=NULL, last_built=2026-09-08`,
  rows_written=240. **"not instrumented" is a legal value** (tier 4 §1); the census records FAIL.
- **History:** latest complete; 7 errors / 8 aborts on record ("BLOCKED: upstream ga_dashas did
  not complete").

### 1.1 · Concept completeness

Universe: **not declared anywhere reachable** — census `Complete.width: NOT_GENERIC` ("no declared
universe for this asset — declaring one is the first width gap"). For a Tājaka year-lord asset the
universe would be (charts × years covered × the lord-set the tradition names); no tier declares it.

**INVENTED — the declared universe for a varṣaphala year-lord computation, clause that should have
provided it: "Declare the universe first, from a source or from the ontology: how many instances
the concept has … and which dimensions each instance should carry." (tier 4 §1.1).** — INV-L1-16.

### 1.2 · Retrieval reachability

2 modules expose it. Field-level census: `Reach.fields: NOT_GENERIC` ("field-level exposure census
is per-capability; not generic"). Requirement **[TRANSFERS]** to the retrieval plane — recorded as
opportunity, not gap, per tier 4 §1.2. This is the one [TRANSFERS] clause a brief CAN apply
mechanically (tier 4 §1.2 states the gap-vs-opportunity rule explicitly). Contrast INV-L1-11.

## §3 · Obligations specialised

| obligation | satisfied means for ga_tajaka | detector |
|---|---|---|
| Computational correctness | the year-lord for (chart, year) reproduces when derived a second way, within a declared tolerance | D3 — **does not exist** (census NO_DETECTOR) |

## §4 · The nine gates (evaluated from census)

| gate | verdict | evidence (census) |
|---|---|---|
| Ldgr | PASS | `citation_ref` populated 780/780 |
| Idem | PARTIAL | "no idempotency pattern in the writer's own SQL — it likely delegates; verify there" |
| Earn | FAIL (build record) | rows_per_second NULL; status lit without measured rate |
| Null | NOT_MEASURED | census has no null-convention probe per asset |
| Vocab | PASS (rules 1–3: identity key unique; no local map measured — `local_map_candidates: -1`) | declared key 0 duplicates |
| Carr | NO_DETECTOR | D3 applicable (tier 4 L1 row); no detector exists |
| Narr | N/A | emits no prose |
| Dens | PASS | 2 modules, 1 density_contract — the claim "confirmed and catalog-only rows counted separately" verified only as contract presence |
| Build | PARTIAL | registered/contract/target/DAG/count-integrity PASS; history PARTIAL (7 err / 8 abort); completion N/A per census ("no count_sql" — **contradicts** count_integrity PASS in the same census row; census-internal inconsistency, recorded not resolved) |

## §5 · Ledger rows (registered as gaps)

measured/required form per tier 4 §5:

- `ga_tajaka · G-T1 · gap · Carr · measured: NO_DETECTOR (census) / required: "what it computes reproduces a second way" · detector: D3 re-derivation (to be built) · gate: Carr · state OPEN`
- `ga_tajaka · G-T2 · gap · Earn · measured: rows_per_second=NULL (census) / required: a status needs a detector that could read false · detector: asset_throughput rate present · gate: Earn · state OPEN`
- `ga_tajaka · G-T3 · gap · Idem · measured: no pattern in writer SQL (census) / required: delete-then-insert on chart × natural key · detector: SQL pattern at the delegated site · gate: Idem · state OPEN`
- `ga_tajaka · G-T4 · gap · width · measured: NOT_GENERIC, no declared universe (census) / required: five-state census against a declared universe · detector: the census itself once the universe is declared · gate: none directly — feeds layer packet · state OPEN`

## §9 · Opportunity register

| dimension | entry | proof afterward |
|---|---|---|
| build cost | instrument the per-chart rebuild (cost × charts) — first efficiency measure | asset_throughput carries rate and duration |
| reachability [TRANSFERS] | field-level exposure census on get_tajik.ts | census re-run per capability |

## §6 · Change packet — not authorised (pilot)

```
may_touch:      platform/python-sidecar/**/ga_tajaka.py (writer; its delegated idempotency site)
must_not_touch: pipeline/orchestrator/** · applied migrations · the 780 existing rows' values
base:           campaign/nikasha-test HEAD
```

Preserved kernel: per row 12 (INVENTED). Idempotency: L1 convention delete-then-insert on
(chart_id × natural key) — natural key here (chart_id, ayanamsha_id, build_id, varsha_year).

## §2 · Shape

identity ✓ inputs/DAG ✓ correctness ✓ data sufficiency ✓ consumers ✓ value/target ✓ synergy ✓
knowledge-time ✓ (varṣa_year is the axis) change packet ✓ evidence ✓

## §7 · Certification — none (pilot; layer instance not ACCEPTED)

## §8 · Review — unsigned. Derivability: **5 of 13 rows clean** (2, 5-partial counted against, 6,
11 partial); rows 1, 8, 12, 13 invented; 9–11 absent instruments (no harness — not chargeable to
this layer instance). Row 13: **C-9 confirmed for L1, fourth surface** — the concept name was
invented; the check class (D3) was inherited from tier 4's L1 adaptation row, which is the only
partial mitigation the documents provide.
