---
artifact: MI_BHARA_BRIEF_TEST
tier: 4
kind: instance — TEST ARTEFACT, NOT A BRIEF
status: PILOT_DRAFT (derivability test only)
produced_on: 2026-09-26
template: 00_ARCHITECTURE/briefs/nirmana/ASSET_ELEVATION_TEMPLATE_v2_0.md
layer_instance: nikasha_test/derivations/L5_INSTANCE_SKELETON.md (TEST ARTEFACT — not ACCEPTED, therefore pilot)
pilot: yes
measured_on: 2026-09-26
measured_against: "census nikasha_test/census/L5_prod_20260926.json; sandbox census agrees"
verdict: NONE
edge_kind_tested: shared/cross-layer target table + registry-writer disagreement + never-lit upstream dependency
---

# mi_bhara — asset elevation brief (TEST ARTEFACT)

## §0 · Identity and inheritance

```
asset_id: mi_bhara · layer: L5 Mīmāṃsā · pilot: yes
kind: INVENTED (see §8 row K1) · scoring_mode: contribution · role: INVENTED
measured_on: 2026-09-26
```

**The three sources disagree (campaign three-source rule):** registry declares `has_writer=true`; code contains **no** `@register('mi_bhara')` (census Build.registered FAIL); run history shows 64 runs (asset_set, global), last 2026-08-21, latest **error**. A writer that was dispatched 64 times but cannot be found in code is a three-way disagreement, and the disagreement is the finding.

**C-10/R06/R10 confirmed for L5:** `target_table = kala_field_skill` — a `ka_`-prefixed table produced (at least nominally) by an `mi_` asset, keyed on `(id)` with no chart scope. Whether `ka_kshetra` or another L3 writer also writes it cannot be told from the census; no contract vocabulary expresses "one table, several producers". Tier-3 §1.1 clause: "For each: target table(s) — a **set**, not one pointer, for multi-table assets" — covers several-tables-one-asset, never several-assets-one-table.

### 0.1 · Inherited — thirteen rows

| # | what | value | from |
|---|---|---|---|
| 1 | P/V | INVENTED (layer 0.1 itself invented) | layer §0.1 |
| 2 | obligations | predictive performance · operational honesty | product §11 — provided |
| 3 | correctness + switch | L5 row (no outcome leakage); the column `skill_prospective` (never populated) reads exactly like the leakage-sensitive field and the template gives no rule connecting them — connection INVENTED | layer §2.1 |
| 4 | presentation fields | INVENTED | layer §2.2 |
| 5 | contracts | consumes ka_kshetra (dep, not lit — DEP-ASSERT trap candidate); declared use INVENTED | layer §2.3 |
| 6 | coverage + state | INVENTED | layer §2.4 |
| 7 | position + baseline | census: 64 runs, latest error 2026-08-21, blocked on ka_kshetra | census |
| 8 | disposition + must-add | INVENTED — though the evidence suggests Q (qualify: no writer, shared table) or U | layer §3.2/3.3 |
| 9 | individual term | absent instrument | layer §1.2 |
| 10 | synergistic term | absent instrument | layer §1.3 |
| 11 | cross-layer term | served: 0 modules (Dens.served N/A) | census |
| 12 | preserved kernel | INVENTED — for a 7-row shared table with no writer, the kernel question (whose rows are whose?) is unanswerable without the multi-producer clause of R06 | layer §3.2 |
| 13 | concepts + carriage check | INVENTED — **C-9/R09 confirmed (sixth time)**: census Carr.detector NO_DETECTOR; nothing assigns D1/D2/D3 | layer §2.7/§4.4 |

### 0.2 · What this asset is for

INVENTED — not writable without inventing ("field-skill scoring carried on a Kāla-named table"). Clause: tier-4 §0.2 "One paragraph, in the layer's terms" — the layer's terms for this asset do not exist above the brief. Per the same section: "If the paragraph cannot be written, the disposition is in question and §5 says so." — §5 row G5 records it.

## §1 · Measured current state

- Storage: `kala_field_skill`, 7 rows, 17 cols, 15 fully populated; NEVER populated: `skill_prospective` (Complete.depth PARTIAL).
- Producer: **none in code**; registry says writer. Tier-4 §1 bullet "Producer: writer module and `@register` id · or the asset it rides on · or 'static, migration N' · or 'service'" — **none of the four alternatives fits** an asset whose writer is declared-but-absent; that is R14-adjacent: the vocabulary covers four kinds and this is a fifth (declared writer, no code). Filled as INVENTED kind: `registry-orphan`.
- Consumers: 1 declared edge, resolvable; actual readers NOT MEASURED; 0 serving modules.
- Baseline: deployed 7 rows, state error; risk/delta NOT MEASURABLE (no current-code read in permitted inputs).
- Build cost: not instrumented (Earn FAIL, rps NULL).
- Evidence state: source-present at best; consumed: nothing demonstrable.

### 1.1 · Concept completeness
Complete.width NOT_GENERIC — no declared universe. NOT MEASURED.

### 1.2 · Retrieval reachability
0 modules; 0 of 7 rows reachable through any declared capability. Reach.fields NOT_GENERIC; [TRANSFERS] requirement; shortfall recorded here as opportunity-shaped, per tier-4 §1.2.

## §2 · Shape
identity ✓ inputs/DAG ✓ correctness ✓ data sufficiency ✓ consumers ✓ value/target ✓ synergy ✓ knowledge-time ✓ change packet ✓ evidence ✓.

## §3 · Obligations specialised

| obligation | satisfied means | detector |
|---|---|---|
| predictive performance | field-skill scores denominated correctly, prospective column separated from retrospective | INVENTED — and note the never-populated `skill_prospective` means the leakage-sensitive half is empty: detector = column census (exists, PARTIAL) |
| operational honesty | the registry does not claim a writer that does not exist | Build.registered (exists, **FAIL**) |

## §4 · Nine gates (from census)

| gate | verdict | evidence |
|---|---|---|
| Ldgr | NOT RUN | — |
| Idem | N/A | "no writer file" — but a bare N/A is a gap per tier-4 §4; the *reason* is the FAIL in Build.registered |
| Earn | FAIL | rows_per_second=NULL |
| Null | NOT MEASURED | — |
| Vocab | PASS | declared key (id): 0 duplicates — key `(id)` surrogate, no chart scope; tier-4 §6 idempotency convention does not fit |
| Carr | NO_DETECTOR | census; row 13 invented |
| Narr | N/A — no prose evidenced | reason stated |
| Dens | N/A | 0 modules — "N/A with reason", correct use |
| Build | **FAIL** | check 1 registered FAIL; check 8 history FAIL (latest error, 19 errors / 4 aborts); check 9 dep_liveness FAIL (`ka_kshetra` not lit — DEP-ASSERT trap). Per tier-4 §4.2 all three are certification-blocking gaps. Blocking radius NOT MEASURED (R21 open). |

## §5 · Delta ledger rows (not registered — test artefact)

- G1 Build.registered FAIL — registry says writer, code has none (three-source disagreement)
- G2 Build.dep_liveness FAIL — ka_kshetra not lit
- G3 Earn FAIL — no build cost instrumented
- G4 Complete.depth PARTIAL — `skill_prospective` never populated
- G5 purpose paragraph unwritable — disposition in question (tier-4 §0.2 rule)
- G6 Carr NO_DETECTOR
- G7 kind vocabulary cannot express this asset (register-orphan) — document gap, tier 4

## §9 · Opportunity register
None — admission rule unsatisfiable from census alone.

## §6 · Change packet
Not authorised. If it were: `must_not_touch` must include the question of who else writes `kala_field_skill` — unanswerable until R06 lands.

## §7 · Certification
None — pilot.

## §8 · Review — unsigned; invention table

| row | invention | clause that should have provided it (verbatim) |
|---|---|---|
| K1 §0 kind | `registry-orphan` kind — none of the template's five kinds fits | tier-4 §0: "kind: data \| service (no table by design) \| multi-table \| rider (producer_covered) \| static (migration-seeded)" |
| K2 §0 role | role unassigned for L5 | tier-4 §0: "role: manifestation \| temporal \| neither (supplies what both rest on)   # from layer §4.4" |
| 0.1.1 | P/V rows | tier-3 §4.4: "the P-needs and V-journeys the asset serves (from 0.1, narrowed)" |
| 0.1.3 | leakage rule ↔ `skill_prospective` linkage | tier-3 §2.1: "For each rule, the detector. A rule with no detector is a wish." |
| 0.1.4 | presentation fields | tier-2 §13.3 item 6: "which §3.4 presentation rows this layer carries and which fields it hands onward for them" |
| 0.1.5 | declared use of ka_kshetra | tier-3 §2.3: "A citation with no declared use is not a contract." |
| 0.1.6 | coverage split | tier-3 §2.4: "Which of the product's coverage obligations this layer owns" |
| 0.1.8 | disposition evidence base | tier-3 §4.4: "its disposition and its 'must add' list (3.2, 3.3)" |
| 0.1.12 | preserved kernel on a shared table | tier-3 §4.4: "the preserved kernel — what of the asset must survive any rebuild unchanged (from 3.2)" + missing R06 clause "a shared table declares its producers and each producer's `count_sql` is scoped to its own rows" (register R06, proposed, not landed) |
| 0.1.13 | carriage check choice | tier-3 §4.4: "the relevant Jyotish concepts the asset touches, named, with the domain detector each invites (2.7, 5.2's menu)" — C-9/R09 confirmed |
| §6 idempotency | keying convention for a non-chart-scoped L5 table | tier-4 §6: "**Idempotency** — the layer's convention: L0 `ON CONFLICT` upsert; L1+ delete-then-insert scoped to `(chart_id × natural key)`" |

**Derivability: 1 of 13 rows filled without invention. This edge-kind asset cannot be briefed from the tiers at all without the R06/R09/R14 fixes.**
