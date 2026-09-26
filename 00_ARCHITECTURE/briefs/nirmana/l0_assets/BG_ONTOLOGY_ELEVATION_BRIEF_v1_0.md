---
artifact: BG_ONTOLOGY_ELEVATION_BRIEF
canonical_id: BG_ONTOLOGY_ELEVATION_BRIEF
tier: 4
kind: instance
version: "1.0"
status: PILOT_DRAFT
produced_on: 2026-09-26
template: 00_ARCHITECTURE/briefs/nirmana/ASSET_ELEVATION_TEMPLATE_v2_0.md   # v2.0, DRAFT_PENDING_REVIEW
layer_instance: 00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v3_0.md  # v3.0, DRAFT_PENDING_ACCEPTANCE
pilot: yes   # the layer instance is not yet ACCEPTED — this brief registers ledger rows and certifies nothing (template §0)
role_in_pilot: "First of five. Chosen because every other L0 asset's identity resolves through this one, and because it was the asset most likely to bend the template."
measured_on: 2026-09-26
measured_against: "live asset_registry · production brahma_ontology (read-only) · brahmagyan/l0_ontology.py imported at HEAD 5973d0132 · the two L0 capability modules · asset_throughput"
verdict: NONE   # pilot — no verdict until the layer instance is accepted
---

# bg_ontology — asset elevation brief (pilot 1 of 5)

**Headline: the finding that matters most is not in this asset.** The layer instance recorded
`bg_ontology` as FAILING identity uniqueness (741 rows, 730 distinct `canonical_id`). Measured against
the table's own declared key — `UNIQUE (entity_class, canonical_id)`, a live database constraint — there
are **741 distinct composites and zero duplicates**. The authority is internally consistent. The defect
is in the *detector* the sealed data plane specifies, and in the *consumers* that resolve on
`canonical_id` alone. See §5 rows G02–G04 and §9 O1.

---

## §0 · Identity and inheritance

```
asset_id:         bg_ontology
layer:            L0 Brahmagyan
layer_instance:   MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v3_0.md (DRAFT_PENDING_ACCEPTANCE)
pilot:            yes
kind:             data — but a SHARED table with four producers (§1)
scoring_mode:     fidelity (reference layer)
role:             neither manifestation nor temporal — it supplies the vocabulary both rest on
measured_on:      2026-09-26
measured_against: registry · production · code at 5973d0132 · capability modules · asset_throughput
```

### 0.1 · Inherited, not re-derived — the thirteen rows

| # | what | value | from |
|---|---|---|---|
| 1 | P-needs and V-journeys | **Directly:** P16/P17 (the concept map an exact lookup and an omission check expand against), P22 and P15 (the *identity* half — which text, which school), P20 (method identity). **Indirectly: every row of the layer's 0.1**, because each resolves its names here. V01 (role vocabulary), V08 (source identity). | layer §0.1, narrowed |
| 2 | obligations scored on | **source and domain fidelity** (primary) · **operational honesty** (it is the id authority; a description asserting a provenance the row lacks is its defect) · **delivery fidelity** (2 served modules). **Not** computational correctness — it computes nothing. | layer §0.2 |
| 3 | correctness rules + switch | "private observations never become global doctrine": **PASS structurally** — no `chart_id`/`subject_id` column. Switch ON/OFF identical: nothing here derives from life events. No invented identity (product §13). | layer §2.1 |
| 4 | presentation fields it must carry | the **closed alias set** — the §3.4 row "one identity rendering as *Śukra* and as Venus"; and, for the `school`/`text` classes, the school or tradition a finding rests on | layer §2.2 |
| 5 | contracts | **produces DP01 identity/release** to every layer, adapter and writer. **Consumes none** — L0 receives from no layer. | layer §2.3 |
| 6 | coverage obligations owned | the **identity half** of all thirteen data plane §5 rows; states in §1.1 | layer §2.4 |
| 7 | position + three-way baseline | **first** in the layer's 4.1 order (a root, 0 dependencies); deployed 741 rows · current code = deployed (no unmerged writer change) · target in §6. **Risk = 0.** | layer §2.5, §4.1 |
| 8 | disposition + must-add | **E — enrich/correct.** Must add: a resolvable key contract, doṣa alias sets, a declared universe, declared normalisation. | layer §3.2, §3.3 |
| 9 | individual term (fidelity) | measured in §1 and §4 — **one FAIL (doṣa alias sets), one finding reclassified** (identity, see headline) | layer §1.2 |
| 10 | synergistic term | it is the **right-hand side of seam A** (catalogue → identity). Seam A's health is this asset's key contract; seams B and C resolve through it too. | layer §1.3 |
| 11 | cross-layer term | DP01, read in **30 files** across sidecar, serving and MCP; evidence state **served**, `value evaluated` not reached | layer §1.4 |
| 12 | **preserved kernel** | the 741 rows with their names, descriptions and citations · the 16-class model · the `UNIQUE (entity_class, canonical_id)` constraint · `l0_ontology.py`'s 414-entity declaration | layer §3.2 |
| 13 | **concepts touched + carriage check** | all sixteen entity classes. Carriage check: **D1 source correspondence** (every row carries `source_citation`; does the row match it). D2 N/A — one identity has no second witness. D3 N/A — nothing is computed. | layer §2.7, §4.4 |

### 0.2 · What this asset is for

It is the plane's dictionary. Every other asset, writer, service and served answer names things through it;
without it each would carry its own spelling of Venus, its own notion of what a varga is, and no join
across the estate would be possible. Removing it does not degrade a reading — it fragments the estate into
pieces that cannot be joined, which is the failure the product's whole differentiator rests on avoiding.

---

## §1 · Measured current state

```
measured_by: per figure below, each naming its population
traces_to:   layer §0.3
```

- **Storage:** `brahma_ontology` — **741 rows** (its own `count_sql`, run 2026-09-26), floor 737, **Δ +4**.
  9 columns: `id, entity_class, canonical_id, canonical_name_en, canonical_name_sa, synonyms, description,
  source_citation, created_at`. Declared key: **`UNIQUE (entity_class, canonical_id)`**. `count_sql`
  (`SELECT count(*) FROM brahma_ontology`) is arithmetically truthful and **semantically misleading** —
  see the next line.
- **Producer — and this is the finding:** `writers/bg_ontology.py` (`@register('bg_ontology')`, `run(ctx)`,
  delegates to `brahmagyan/l0_ontology.py::seed_ontology`, `autocommit=False`, orchestrator owns the
  transaction — frozen contract conformant). Its `ENTITIES` list, imported at HEAD, declares **414 rows
  across 14 classes**. Production holds **741 across 16**. The difference is **327 rows this writer does
  not produce**: `yoga` 233 and `dosha` 79 (two classes it never declares) and 15 extra `dasha_system`
  rows (it declares 5; production has 20). Grep confirms three further producers of the same table:
  `l0_yogas.py`, `l0_doshas.py`, `l0_dasha_systems.py`. **`brahma_ontology` is a shared table with four
  producers, and `bg_ontology` is credited in the cockpit with all 741.**
- **Consumers, declared vs actual:** registry `depends_on` — `bg_reference` declares it; the registry
  records few edges into it. Actual: **30 files** reference `brahma_ontology` across
  `platform/python-sidecar`, `platform/src`, `platform-mcp/src`. The gap is the layer instance's §1.4
  finding in one asset.
- **Served surface:** **2 capability modules** — `resolve_entity.ts`, `list_entities.ts`. **Neither
  declares a `density_contract`** (0 of 2; 0 of 46 layer-wide).
- **Three-way baseline:** deployed 741 rows / 16 classes · current code identical (no unmerged change to
  `l0_ontology.py` on any live head) · target §6. **Delta = target − current code; risk = 0.**
- **Evidence state:** source-present ✓ · qualified ✓ · consumed ✓ (30 files) · traceably transformed ✓ ·
  served ✓ (2 modules) · **value evaluated ✗** — no ablation has been run.
- **Build-cost baseline: NOT INSTRUMENTED.** `asset_throughput` for `bg_ontology` reads
  `state=lit, rows_written=0, rows_per_second=NULL, last_built_at=2026-09-04` — a zero row count for a
  741-row table. The record exists and carries no usable cost figure; the instrument is opportunity O4.

### 1.1 · Concept completeness — width and depth

```
measured_by: depth = six content dimensions × sixteen classes over all 741 rows · width = per-class member lists against a declared universe, and two cross-authority checks
traces_to:   layer §2.4
```

**Depth — 6 dimensions × 16 classes, one cell fails.** Every class is fully populated on
`canonical_name_en`, `canonical_name_sa`, `description` and `source_citation` (0 missing anywhere).
`synonyms` is populated for 15 classes and **empty for all 79 `dosha` rows** — the class a doṣa name
lookup must resolve through.

**Width — the universe is NOT DECLARED, and that is the first gap.** Nothing in the asset or the layer
states how many members each class should have, so "is this class complete?" has no answer for 11 of the
16. What can be measured:

| class | measured | width verdict |
|---|---|---|
| `upagraha` | 11: ardhaprahara, dhuma, gulika, indrachapa, kala, maandi, mrityu, parivesha, upaketu, vyatipata, yamaghantaka | **complete** against the standard eleven |
| `sign` 12 · `house` 12 · `nakshatra` 27 | the closed classical sets | **complete** |
| `planet` | 11 = the 9 grahas **+ `ascendant` + `midheaven`** | **undeclared modelling choice** — two calculated points sit in a class named for grahas. Legitimate, but until it is declared, the class's completeness is unanswerable |
| `varga` | 30: d1–d60 plus d108, d150, d2700 | beyond the ṣoḍaśavarga 16; **universe undeclared** |
| `text` | 15 | **FAILS a cross-authority check — see below** |
| `dasha_system` | 20 in production, **5 declared by this writer** | the other 15 come from `l0_dasha_systems.py`; neither declares a universe |
| `yoga` 233 · `dosha` 79 · `concept` 136 · `domain` 45 · `karaka` 77 · `aspect_type` 13 · `remedy_type` 12 · `school` 8 | catalogue-defined | **universe undeclared**; a count is not a coverage claim |

**The cross-authority check a row count would have missed.** The `text` class holds 15 members and the
corpus holds 15 `text_id`s — equal counts, **and the sets differ by three in each direction**:

- in the ontology, no text in the corpus: `bhrigu_samhita`, `jaimini_sutram`, `lal_kitab_text` — three
  declared identities with no text behind them;
- in the corpus, no identity in the ontology: `bhrigu_nandi_nadi`, `bphs_jaimini`, `nadi_navamsa_patel` —
  three texts we hold that cannot be named through the controlled set.

The second set is also two of the unresolved values behind the layer's 289-row remedy finding, so this is
one defect surfacing in two places. **15 = 15 would have read as complete.** This is the width census
earning its place.

### 1.2 · Retrieval reachability — everything built, reachable

```
measured_by: exposure census over the two capability modules serving this asset — fields selected vs columns built; class vocabulary and pagination vs rows built
traces_to:   layer §1.4
```

- **Fields: 7 of 7 content columns exposed.** `resolve_entity` selects `canonical_id, entity_class,
  canonical_name_en, canonical_name_sa, synonyms, description, source_citation`. `id` and `created_at` are
  internal plumbing, not content. Field reachability is complete.
- **Rows: 233 of 741 are unreachable, and the tool explains why with a false statement.**
  `list_entities` carries `UNBACKED_CLASSES = {'yoga','karana'}` and returns an empty array with an
  `empty_reason` asserting that `yoga` *"has no dedicated top-level class in brahma_ontology — it exists
  only as a single canonical_id='yoga' row under entity_class='concept'"*. Production has **233 rows with
  `entity_class='yoga'`**. The honest-empty mechanism is serving an invented fact.
- **79 further rows are reachable but undeclared.** `dosha` is absent from `VALID_ENTITY_CLASSES`, so it
  passes through the filter and matches its 79 rows at runtime while a caller reading the tool's own
  vocabulary would never know to ask for it.
- **Measured reachability: 429 of 741 rows (58%) reachable *and* declared**; 508 (69%) reachable at
  runtime. Pagination itself is sound (limit 100 / max 500, cursor with a facet fingerprint).
- The *requirement* that all width and depth be reachable is **[TRANSFERS]** to the retrieval plane. The
  false `empty_reason` is not a transfer — a served surface making a measurably untrue assertion is a
  defect now (G06).

---

## §3 · The asset's own obligations, specialised

| obligation | what satisfied means for `bg_ontology` | detector |
|---|---|---|
| Source and domain fidelity | every row's `source_citation` names a real source and the row's content matches it | D1 source correspondence — **does not exist** (G05) |
| Operational honesty | the cockpit credits this asset with what its writer produces, and its build record carries a real figure | `count_sql` scoped to this writer's own rows (G01); `asset_throughput.rows_written` non-zero after a build (O4) |
| Delivery fidelity | every class built is reachable and declared through the served surface, both renderings derivable from the alias set | the §1.2 exposure census (G06, O3) |

---

## §4 · Asset conformance — the eight gates

| gate | verdict | detector and evidence |
|---|---|---|
| **Ldgr** derivation ledger | **PASS** | L0 is the root, so the gate reads as source presence: `source_citation` populated on 741/741 rows (query, 2026-09-26). No upstream `fact_id` applies. |
| **Idem** idempotency | **PASS** | `l0_ontology.py` L1119/L1123: `ON CONFLICT (entity_class, canonical_id) DO NOTHING` / `DO UPDATE SET` — the L0 upsert convention (§N.3), matching the table's declared key. A rebuild replaces its own rows. |
| **Earn** earned signal | **PARTIAL** | `count_sql` and `integrity_check_sql` both present and able to fail. But `asset_throughput.rows_written = 0` against 741 live rows is a status carrying no measurement (G02), and the `empty_reason` in §1.2 is an unearned assertion (G06). |
| **Null** honest null | **PASS** | `resolve_entity` returns explicit nulls and an empty `synonyms` array on no-match rather than a plausible substitute (L78–84). |
| **Vocab** vocabulary conformance | **FAIL** | Applicable §4.1 rules for this asset: **1, 2, 3** (a data asset, and the authority itself), **not 4** (ships no code-side snapshot), **not 5** (its interface parameters are the served modules', measured in §1.2), **6 N/A** (it *is* the map). Rule 1 alias half: **FAIL** — 79/79 doṣa rows without an alias set. Rule 1 identity half: **PASSES under the declared composite key**; the detector the data plane specifies is the wrong one (G03). Rule 3: **FAIL** — normalisation is not declared at the authority; `BPHS` vs `bphs` is why 289 remedy ids do not resolve. |
| **Carr** source carriage | **NO_DETECTOR** | D1 is the applicable check (row against its cited source). Nothing compares them. D2 N/A — a single identity has no second witness. D3 N/A — nothing computed. (G05) |
| **Narr** narration fidelity | **N/A** | `description` is seeded editorial prose, not narration re-derived over computed facts; §N.7's defect class does not apply. It *is* in scope for D1 once that detector exists — recorded so the N/A is not read as "never checkable". |
| **Dens** serving density | **FAIL** | Applies — the asset reaches a served surface. Neither of its 2 capability modules declares a `density_contract`; and 233 built rows are unreachable through one of them (§1.2). |

---

## §5 · The delta ledger — this asset's rows

Registered in `00_ARCHITECTURE/control/asset_gaps.jsonl`. Rendered here, not retyped.

| gap_id | kind | criterion | what (measured / required) | gate it blocks |
|---|---|---|---|---|
| `bg_ontology-G01` | gap | Earn.count_sql_scope | measured: `count_sql` returns 741, of which 327 rows are produced by three other writers / required: the cockpit credits an asset with its own rows | this asset's certification |
| `bg_ontology-G02` | gap | Earn.build_record | measured: `asset_throughput.rows_written = 0` against 741 live rows / required: a build record carrying a real figure | this asset's certification |
| `bg_ontology-G03` | gap | Vocab.rule1.detector | measured: data plane §4.1 rule 1's detector is `count(*) = count(DISTINCT canonical_id)` across classes, which FAILS data satisfying its own `UNIQUE (entity_class, canonical_id)` / required: a detector that tests the authority's declared key | **layer packet + a sealed-document reopen** |
| `bg_ontology-G04` | gap | Vocab.rule2.consumer_key | measured: `resolve_entity.ts` returns two rows for 11 ids and applies a hard-coded `ORDER BY (entity_class='varga') DESC` preference — for `navamsa`, which exists in ONE class only, so the workaround addresses a condition not present / required: consumers resolve on the declared composite key, or the key is made simple | W-L0-5 |
| `bg_ontology-G05` | gap | Carr.D1 | measured: no detector compares a row to its `source_citation` / required: one that can fail | W-L0-3 |
| `bg_ontology-G06` | gap | Dens + Earn | measured: `list_entities` returns `empty_reason` stating `yoga` has no top-level class, against 233 such rows; `dosha` absent from `VALID_ENTITY_CLASSES` while matching 79 rows / required: a served surface's stated reason is true | this asset's certification |
| `bg_ontology-G07` | gap | Vocab.rule1.alias | measured: 79 of 79 doṣa rows with an empty `synonyms` array / required: a non-empty closed alias set per entity | W-L0-5 |
| `bg_ontology-G08` | gap | Vocab.rule3 | measured: normalisation undeclared at the authority; 289 remedy ids fail on case alone / required: the rule declared once, at the authority | W-L0-5 |
| `bg_ontology-G09` | gap | Completeness.width | measured: no declared universe for 11 of 16 classes; `text` class and corpus differ by 3 in each direction / required: a declared universe per class, and the two sets reconciled | this asset's certification |
| `bg_ontology-G10` | gap | Dens.density_contract | measured: 0 of 2 capability modules declare one / required: declared where the capability paginates or facets | W-L0-8 |

## §9 · Opportunity register

| id | dimension | what it would add / remove | proposal | proof afterward |
|---|---|---|---|---|
| `O1` | **architecture** | removes the class of defect behind G03, G04 and the layer's mis-stated finding, permanently | **Settle the key contract as one decision**, three options: (a) keep the composite key and make every resolver and join class-aware; (b) make `canonical_id` globally unique and rename the 11 collisions; (c) keep the composite key and add a generated `global_id` (`class:id`) for consumers that need one token. (a) matches the writer's intent and the live constraint, and is cheapest; (b) matches data plane §4.1 rule 1 as literally written. **This is a native decision, not an asset fix.** | after: every consumer join resolves to exactly one row for all 741 identities, measured by a join census; before: 11 ids return two |
| `O2` | **architecture** | one authority, one producer — removes the provenance ambiguity behind G01 | Either split the ontology's identity rows so each class has one producer, or declare `brahma_ontology` a **multi-producer shared table** in the registry and give `bg_ontology` a `count_sql` scoped to its own 414 | a per-class producer census; `count_sql` output equals the writer's own declared row count |
| `O3` | **reachability** | makes 312 built rows (233 yoga + 79 doṣa) reachable and declared | add `yoga` and `dosha` to `VALID_ENTITY_CLASSES`, delete the false `UNBACKED_CLASSES` branch. **[TRANSFERS]** — the requirement is the retrieval plane's; the measurement is here | the §1.2 census re-run: reachable-and-declared 429/741 → 741/741 |
| `O4` | **build cost** | a real cost baseline where none exists | instrument the seeder's run: rows written and duration into `asset_throughput`, replacing `rows_written = 0` | the record carries a non-zero row count and a duration after one build; output parity unchanged (414 declared rows still seeded) |
| `O5` | **algorithm** | fewer inputs, less drift | the 414 entities are a Python literal list; the 15 `text` members duplicate what `classical_text_chunks` already knows, and the two sets have drifted by 3. **Derive the `text` class from the corpus** instead of declaring it twice | the two sets agree by construction; re-running the §1.1 cross-check returns 0 in both directions |
| `O6` | **synergy** | one join instead of four | `bg_yogas`, `bg_doshas` and `bg_dasha_systems` each seed identity rows here *and* keep their own catalogues. A declared identity contract between them — catalogue rows referencing the ontology by composite key — would make seam A provable rather than assumed | ablation of seam A: break the identity reference and measure the served reading; today the seam cannot be broken because it is not declared |

**Admission check:** every row above states its measurement-after. `O1` is a decision, not a build, and is
recorded as an opportunity because its *value* (one resolvable identity) is measurable either way.

---

## §6 · Change packet — not authorised by this brief

```
may_touch:      platform/python-sidecar/brahmagyan/l0_ontology.py · platform/src/lib/retrieval/registry/layers/L0_brahmagyan/{resolve_entity,list_entities}.ts · a new governance detector · one migration for alias rows
must_not_touch: platform/python-sidecar/pipeline/orchestrator/** (frozen contract) · the other three ontology producers (their own briefs) · any applied migration
base:           5973d0132
```

- **Preserved kernel:** the 741 rows with names, descriptions and citations; the 16-class model; the
  `UNIQUE (entity_class, canonical_id)` constraint; the writer's `@register` conformance and its
  `autocommit=False` boundary.
- **Exact delta (target):** 79 doṣa alias sets · a declared universe per class · normalisation declared
  at the authority · `count_sql` scoped to this writer's rows · the D1 detector · two capability fixes.
- **Writer conformance:** already conformant — `@register('bg_ontology')`, `run(ctx)`, `ctx.db_conn` never
  committed by the writer. **Nothing here needs the frozen contract changed.**
- **Idempotency:** L0 upsert on the declared composite key — unchanged.
- **Migration:** alias rows are data, seeded by the writer; if a migration is needed its number is
  scanned at execution across every `origin/*` head and both directories, never trusted from this document.
- **Rollback:** re-seed. No chart is involved. The key decision (O1) is not rollback-safe once consumers
  change — it is the one item that needs its own decision record.
- **Consumer impact:** 30 files read this table; the two served modules change; the key decision touches
  every join on `canonical_id`.
- **Open decisions:** O1 (the key contract) — native. O2 (multi-producer declaration) — native or the
  layer packet.

---

## §2 · Brief shape — self-check

identity ✓ · inputs/DAG ✓ · correctness ✓ · data sufficiency ✓ · consumers ✓ · value/target ✓ ·
synergy ✓ · knowledge-time ✓ (no `as_of` dimension — stated) · change packet ✓ · evidence ✓

## §7 · Certification records

**None, and none permitted.** This is a pilot brief (§0): the layer instance is not accepted, so no
criterion may be certified from it. Ten gap rows and six opportunities are registered instead.

## §8 · Review and signature

**Unsigned.** What this pilot proves about the template and the instance is recorded in the pilot findings
appended to the layer instance's Part 6, not here — a brief does not review its own parents.

**Derivability result (the test this pilot exists for): 12 of 13 inheritance rows filled without
invention.** Row 13's carriage check had to be *chosen* (D1, with D2 and D3 marked N/A) because the layer
instance names the three checks at layer scope but does not assign one per asset. That is a defect in the
instance, not in this brief — recorded as its own correction.
