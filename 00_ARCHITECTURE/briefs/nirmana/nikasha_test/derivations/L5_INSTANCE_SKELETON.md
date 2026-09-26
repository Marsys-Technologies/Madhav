# TEST ARTEFACT — NOT AN INSTANCE

# L5 Mīmāṃsā — Layer Definition and Strategy (SKELETON, derivability test)

- derived by: fresh reader, Nikaṣa Phase 4, 2026-09-26
- sources permitted: tier-1/tier-2 summary (`_tier1_tier2_summary.md`), tier-3 template (SEALED), tier-4 template v2.0, census `nikasha_test/census/L5_prod_20260926.json` (production; sandbox `L5_sandbox_20260926.json` also exists, values agree on all verdict fields)
- rule: `INVENTED — <what>, clause that should have provided it: "<verbatim quote>"` wherever a value was supplied from outside those sources.

---

## Part 0 · VALUE

### 0.1 · What cannot be answered without this layer

```
inherits:    Product §2 (P01-P24), Data plane §2 (V01-V13)
measured_by: none — definitional
traces_to:   —
```

Tier 1 §11 gives L5's row ("Challenge, adjudication, scope of validity and qualified learning") and tier 2 §3.1 gives the owned question ("What withstands challenge, observation and independent evaluation?"). **Neither parent names which P-needs / V-journeys L5 is necessary to.**

INVENTED — the P/V row assignment below, clause that should have provided it: tier-3 §0.1 "List the P-needs and V-journeys for which this layer is **necessary**" — the template demands a per-layer necessity list that no tier-1/2 table assigns per layer (§11 assigns proofs, §3.1 assigns questions, neither maps P01–P24 / V01–V13 to layers).

| P / V | the distinction that disappears without this layer | source |
|---|---|---|
| (invented) P-needs around "has this forecast been tested / did it hold" | no preserved claim, no adjudication, no honest "we were wrong" | INVENTED from §3.1 row's substance |
| (invented) V-journey(s) around performance evidence and study candidates | evaluation evidence is L5's alone (DP15b) | INVENTED from DP15a/DP15b producer→consumer column |

### 0.2 · The layer's objective

```
inherits:    Product §1, §11 (L5 row), Data plane §3.1 (L5 row)
measured_by: none — definitional
traces_to:   0.1
```

- Owned question (verbatim, tier 2 §3.1): "What withstands challenge, observation and independent evaluation?"
- Hands onward: "Preserved claims/outcomes, fit/misfit, admissible performance evidence, study candidates and separately approved future model artifacts."
- Must not claim: "Feedback capture as learning, retrospective fit as prediction, evaluation outcomes as serving context."
- Scored on (tier 1 §11, inherited not invented): **Predictive performance + Operational honesty** — "preserved failures, independent evidence, correct denominators, leakage-free evaluation."

Provided by parents; no invention in this section.

### 0.3 · Its place in the wheel

```
inherits:    Data plane §3.2, §7
measured_by: census L5_prod_20260926.json (registry three-source reconciliation NOT run — census reads registry + code only; migration pin NOT READ)
traces_to:   0.2
```

- **Receives from:** evaluation edge (§3.2 edge 4: "frozen claims and purpose-admitted observations into protected comparison"); observation intake via DP13; historical comparison via DP14. Census-declared intra-plane inbound edges include `ph_nimitta`, `ph_phaladesa`, `ph_pramana` (L4), `ka_kshetra`, `ka_sangam` (L3) — every one currently reported not-lit by `Build.dep_liveness`.
- **Hands onward:** DP15b later evaluation ("protected L5"); next-generation artifact edge (edge 5) — "separately approved future model artifacts".
- INVENTED — the per-layer produced/consumed DP-contract split is assembled by the reader from the §7.1 producer→consumer column; clause that should have provided it: tier-2 §13.3 item 6 "Upstream demand and downstream offers with field/grain/context/lineage contracts, named owners and tests" — no per-layer contract-assignment table exists above the instance.

**Three-source rule status (template 0.3 `measured_by`):** only ONE of the three mandated sources (live registry via census) was available in the permitted inputs; the seed and the migration pin were not read. INVENTED — nothing; recorded as NOT MEASURED. Clause that makes this a hole: tier-3 §0.3 "registry depends_on reconciled across seed, migration pin AND live asset_registry — state all three and any disagreement."

### 0.4 · Alignment test

Skeleton only; not run.

---

## Part 1 · VALUE DECOMPOSITION

### 1.1 · Inventory, measured

```
inherits:    Data plane §13.3 item 2
measured_by: census L5_prod_20260926.json (the inspector over live asset_registry + build_runs/build_run_assets + asset_throughput)
traces_to:   0.3
```

14 assets, all `has_writer=true` in the registry; 12 `@register` ids found in code. **Disagreement: `mi_bhara` and `mi_sankalpa` — registry says writer, code has none (Build.registered FAIL).** `local_map_candidates = -1` (not measured). `never_exercised_with_writer = []`.

| asset | target_table | live_rows | notes from census |
|---|---|---|---|
| mi_abhilekha | mimamsa_journal | null (not counted) | DRAFT; Idem PARTIAL (delegation); dep mi_bhavisya not lit |
| mi_adhilepa | mimamsa_load_bearing | 9 | latest run error; deps mi_gunanaka, ka_sangam, ph_nimitta not lit |
| mi_bhara | **kala_field_skill** | 7 | **no writer file; target table carries another layer's prefix — shared/cross-layer table (C-10 confirmed for L5)**; dep ka_kshetra not lit; column `skill_prospective` never populated |
| mi_bhavisya | mimamsa_predictions | 195 | latest error; deps ph_* not lit; `base_rate`, `contact_id` never populated |
| mi_darshana | mimamsa_insight_units | 150 | latest error; five deps not lit |
| mi_gunanaka | mimamsa_multipliers | 18 | latest error; dep mi_pramana not lit |
| mi_jivanaghatana | mimamsa_event_provenance | 63 | 6 columns never populated; lit; deps lit |
| mi_kula | mimamsa_signal_families | 15 | completion PASS (15=15); healthiest asset in layer |
| mi_pariksha | mimamsa_qa_eval | 174 | latest error; dep mi_pramana not lit |
| mi_pramana | mimamsa_calibration | 57 | latest error; dep mi_bhavisya not lit |
| mi_sambandha | mimamsa_manifestation_grammar | 47 | latest error; Ldgr.source_presence PASS 47/47 |
| mi_sankalpa | mimamsa_intervention_ledger | 0 | **no writer file**; dormant; dep ka_kshetra not lit |
| mi_seva | mimamsa_preferences | 0 | DRAFT; empty; dep mi_adhilepa not lit |
| mi_vistara | mimamsa_export_log | 0 | empty by design or service; no declared dependencies |

**C-10 / R06 / R10 confirmed for L5.** `mi_bhara`'s target `kala_field_skill` is a `ka_`-prefixed table — a shared or cross-layer table with (potentially) several producers, and the census's `count_sql`/live_rows read cannot attribute rows to a producer. Clause that should have expressed it: tier-3 §1.1 "For each: target table(s) — a **set**, not one pointer, for multi-table assets" (no expression for several-assets-one-table; register R06/R10, OPEN).

**Floors:** census gives `Count.floor` only for mi_kula (15/0) and mi_seva, mi_vistara (0/0); the remaining 11 assets carry no floor reading — floors not provided by any permitted document. NOT MEASURED, not invented.

### 1.2 · Individual contribution

NOT MEASURABLE from permitted inputs — no ablation harness exists and the census measures conformance, not contribution. L5 is a chart-product layer (`scoring: contribution` in census), so fidelity carve-out does not apply. Per template §1.2: "where no served path exists, state 'unmeasurable — not reached'". Served paths exist for 9 of 14 assets (Dens.served PASS lists modules), so ablation is the owed instrument and is absent. Recorded as absent instrument, not zero.

### 1.3 · Synergistic contribution

Absent instrument (same as L0's W-L0-7 finding). Seam candidates visible from census only: mi_sambandha's `citation_ref` 47/47 (source-presence seam); the dep graph among mi_* assets (darshana ← adhilepa, gunanaka, pariksha, pramana, sambandha). No fraction recorded. Clause honoured: tier-3 §1.5 "Record the synergistic term as a fraction of the total **only where an ablation harness exists to produce it**."

### 1.4 · Cross-layer handoff

Evidence-state positions from census only: `consumed`/`served` demonstrable for mi_bhavisya (5 modules), mi_pariksha (4), mi_pramana (4), mi_darshana (3), mi_sambandha (3), mi_adhilepa (2), mi_kula (2), mi_abhilekha (1); 0 modules for mi_bhara, mi_jivanaghatana, mi_sankalpa, mi_seva, mi_vistara. "Verified at the consumer, not asserted by the producer" (template §1.4) — NOT RUN; the census counts modules, it does not verify the consumer reads. `value evaluated` reached by none.

### 1.5 · The accounting

Cannot be closed: 1.2 and 1.3 are absent instruments. The shortfall against 0.2 is therefore stated qualitatively: L5's objective (claims that withstand challenge) is blocked at the *build* level today — 8 of 14 assets' latest run is error, and the dep-liveness FAILs form a cycle-cluster around mi_bhavisya/mi_pramana (mi_bhavisya ← ph_*; mi_pramana ← mi_bhavisya; mi_abhilekha ← mi_bhavisya; mi_gunanaka, mi_pariksha ← mi_pramana). This is a layer-level finding the census provides directly; no invention needed.

---

## Part 2 · CONDITIONS UNDER WHICH THE VALUE IS REAL

### 2.1 · Correctness rules

```
inherits:    Product §8.1 (L5 row), §13; Data plane §9.2
measured_by: detector per rule — none run in this derivation
traces_to:   0.2
```

- L5's §8.1 row (from tier-1 summary): **"no outcome leakage into prospective generation."** Detector: none named in any permitted document for L5. INVENTED — nothing; recorded NO DETECTOR. Clause: tier-3 §2.1 "For each rule, the detector. A rule with no detector is a wish."
- Life-event switch: tier-4's L5 adaptation row supplies the layer's two load-bearing rules verbatim: "the firewall — admitted outcomes never enter provider synthesis; a rebuild never re-stamps emission time" (tier-4 "Adapting per layer", L5 row). Switch ON/OFF emission behaviour for L5 specifically: INVENTED — per-layer switch behaviour text, clause: tier-3 §2.1 "what this layer may do when ON, what it emits when OFF, and the storage separation that makes OFF a selection rather than a rebuild" — the parents define the switch (product §8) but not its per-layer ON/OFF emission semantics.

### 2.2 · Presentation obligation

Which §3.4 presentation rows L5 carries: not assigned anywhere above the instance. INVENTED — the L5-carried rows (candidate: none of the eight rows name evaluation evidence; L5 arguably carries none, or carries "competing readings with their authorities" for rival propositions under DP14). Clause: tier-2 §13.3 item 6 "including which §3.4 presentation rows this layer carries and which fields it hands onward for them" — the obligation to state it exists; the assignment does not. This is a **chart-product-layer-shaped** requirement: §3.4's rows are all reading-rendering fields; an evaluation layer has no acharya-rendering surface, and the template gives no rule for a layer whose answer is "none".

### 2.3 · Contracts produced and consumed

From tier-2 §7.1 producer→consumer column (derivable, partially):
- **Produces:** DP15b (later evaluation, "protected L5"); shares DP14 (historical comparison); receives DP13 observations and DP15a protected claims.
- **Consumed:** DP09 manifestation (from L4 — census confirms ph_* deps), DP08 temporal mechanism (L3 — ka_* deps), DP06 structural relationship (L2).
- INVENTED — field/grain/identity/generation per contract and the "declared use" per consumed contract, clause: tier-3 §2.3 "Every consumed input declares its use … **A citation with no declared use is not a contract.**" — no parent provides per-layer declared uses.

### 2.4 · Jyotish coverage owned

INVENTED — L5's owned subset of the §5 domain obligations. Clause: tier-3 §2.4 "Which of the product's coverage obligations this layer owns" — neither the summary's §5 extract nor §11 assigns domain-coverage rows per layer; L0's instance had to assign its own ("the meaning half"), and no rule for that halving exists above the instances.

### 2.5 · Edges and order

Census provides per-asset edge counts and resolvability (all PASS, 0–8 edges). Topological order not computed by the census — derivable from declared deps: cycle-cluster noted in 1.5 is an ordering *fault* only if deps are unlightable (Build.dep_liveness FAIL for 9 of 14 assets). Cross-layer gate state via `egate.sql`: NOT RUN (instrument named by template; not in permitted inputs).

### 2.6 · Vocabulary conformance

Which of the sixteen entity classes L5 emits or accepts: INVENTED — not stated anywhere (candidates from census keys: `event_class_id`, `intervention_class`, `channel_id`, `origin_kind` — none reconciled against the 16 classes). Census `local_map_candidates = -1` (not measured). Clause: tier-3 §2.6 "Which of the sixteen entity classes this layer emits or accepts" — requires a per-layer class assignment no parent contains.

### 2.7 · Source carriage and reproduction

Layer scope, from census: **`Carr.detector` = NO_DETECTOR for 14 of 14 L5 assets** — "no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics". Per-asset assignment (which of a/b/c each asset invites): **C-9 / R09 CONFIRMED FOR L5** — tier-3 §2.7 assigns the checks at layer scope only ("For each obligation the layer owns (§2.4), state which of a–c applies"), and §4.4's row 13 demands the per-asset assignment the instance cannot produce without inventing it. Clause quoted: tier-3 §4.4 "the relevant Jyotish concepts the asset touches, named, with the domain detector each invites (2.7, 5.2's menu)" — 2.7's menu is a/b/c at layer scope; the per-asset bridge does not exist.

Note also the wording defect: §4.4 row 13 says "**domain** detector" while the menu is a *carriage* menu (ruling 11 rescoped §2.7 away from domain correctness) — stale vocabulary from before the Dom→Carr rename.

---

## §4.4 · What each asset brief inherits — the thirteen rows, fill status

| # | row | fillable for L5 from tiers + census? |
|---|---|---|
| 1 | P/V the asset serves | **NO** — per-layer P/V necessity was itself invented (0.1) |
| 2 | obligations scored on | **YES at layer scope** (predictive performance + operational honesty, product §11) |
| 3 | correctness rules + switch | **PARTIAL** — §8.1 L5 row + tier-4 L5 adaptation (firewall, re-stamp); per-layer switch ON/OFF invented |
| 4 | presentation fields | **NO** — §3.4 row assignment per layer does not exist (2.2) |
| 5 | contracts produced/consumed with declared use | **PARTIAL** — direction from §7.1; declared uses invented |
| 6 | coverage obligations + states | **NO** — per-layer §5 split invented (2.4) |
| 7 | position in order + three-way baseline | **PARTIAL** — census gives deployed/build state; "current code (newest on any live head, including unmerged)" and "target" not in any permitted source |
| 8 | disposition + must-add | **NO** — requires Part 1 measurements (absent instruments) and the companion contribution register, which was not a permitted input |
| 9 | individual term, measured | **NO** — no ablation harness; "absent instrument" is the honest fill |
| 10 | synergistic term, measured | **NO** — absent instrument |
| 11 | cross-layer term, evidence state | **PARTIAL** — census Dens.served gives served modules; "verified at the consumer" not run |
| 12 | preserved kernel | **NO** — per-asset; nothing above the instance defines it |
| 13 | Jyotish concepts + carriage check each invites | **NO** — C-9/R09 confirmed for L5 (see 2.7); also carries the stale "domain detector" wording |

**Derivability score: 2 of 13 YES, 5 PARTIAL, 6 NO.** A real L5 brief author must invent the majority of the inheritance — the instance skeleton cannot be brought to ACCEPT under §5.4 test 1 from the permitted sources.

### [TRANSFERS] test (brief-mandated)

DP10/DP11/DP12 and the §8 intermediary obligations are marked [TRANSFERS] in tier 2. Test question: can an L5 plan tell what is its own work? **Mostly yes for L5** — L5's [TRANSFERS] surface is small (retrieval reachability of evaluation evidence under DP10; delivery of adjudication under DP12) and tier-2 §1's rule ("A [TRANSFERS] obligation is not a data-plane layer's to build alone, and a layer plan does not inherit it as its own work") is directly applicable. Residual ambiguity: tier-2 §9.1 names the observation-ownership split L5 must resolve (`brahma_prospective_ledger` vs `brahma_mimamsa_prediction_ledger`; `mi_jivanaghatana`; `ph_nimitta`/`mi_bhavisya`) — the parents name the question but assign the resolution to "the L5/intake brief", i.e. the instance must decide an asset-vs-asset ownership that the plane declined to decide. That is work a layer plan *can* identify as its own, but it is a decision no template row tells the brief author it must make.

### Chart-product-only defects visible from L5

Tier-4 §6 idempotency convention: "L1+ delete-then-insert scoped to `(chart_id × natural key)`" — but tier-2 §3.3 explicitly retains "Shared L5 qualification/model resources and global services" with registered scope, and L5's census shows assets whose declared keys are NOT chart-scoped: `mi_kula (family_id)`, `mi_vistara (export_id)`, `mi_bhara (id)`. The L1+ idempotency clause does not fit L5's global-scope assets; an L5 instance must invent its own keying convention for them. Clause: tier-4 §6 "**Idempotency** — the layer's convention: L0 `ON CONFLICT` upsert; L1+ delete-then-insert scoped to `(chart_id × natural key)`."
