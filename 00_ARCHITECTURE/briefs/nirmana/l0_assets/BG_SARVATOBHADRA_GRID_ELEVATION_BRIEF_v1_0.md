---
artifact: BG_SARVATOBHADRA_GRID_ELEVATION_BRIEF
canonical_id: BG_SARVATOBHADRA_GRID_ELEVATION_BRIEF
tier: 4
kind: instance
version: "1.0"
status: PILOT_DRAFT
produced_on: 2026-09-26
template: 00_ARCHITECTURE/briefs/nirmana/ASSET_ELEVATION_TEMPLATE_v2_0.md
layer_instance: 00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v3_0.md
pilot: yes
role_in_pilot: "5 of 5 — an asset that is EMPTY BY DESIGN. Stresses whether abstention is expressible as fidelity rather than as a defect."
measured_on: 2026-09-26
measured_against: "live asset_registry · production bg_sarvatobhadra_grid (0 rows) · migration 529 · asset_throughput · the seating brief"
companion: 00_ARCHITECTURE/briefs/nirmana/SARVATOBHADRA_GRID_SEATING_BRIEF_v1_0.md
verdict: NONE
---

# bg_sarvatobhadra_grid — asset elevation brief (pilot 5 of 5)

**Headline: an empty asset passes fidelity, and the template can say so.** 0 rows, by a standing ruling,
because the 9×9 grid's geometry varies by tradition and no school's version is source-verified. The
abstention *is* the correct output. Every gate below is either PASS-by-abstention or N/A with a reason —
and none of that required inventing a row.

## §0 · Identity and inheritance

```
asset_id: bg_sarvatobhadra_grid · layer: L0 Brahmagyan · pilot: yes
kind: data — DELIBERATELY EMPTY (ADJUDICATION-11) · scoring_mode: fidelity · role: neither
measured_on: 2026-09-26
```

### 0.1 · Inherited — thirteen rows

| # | what | value |
|---|---|---|
| 1 | P/V | **P09** (does this configuration form, and when) via transit vedha; **V04** activation. Today it serves neither — see row 11 |
| 2 | obligations | source and domain fidelity (primary) · operational honesty |
| 3 | correctness + switch | no per-subject rows; switch-irrelevant; **no invented computation or source** — the rule this asset exists to honour |
| 4 | presentation fields | the §3.4 "method and school" row: `school_tag` is the field that would carry it |
| 5 | contracts | **produces** an optional input to DP08 temporal mechanism via `ka_vedha_gochara`; consumes none |
| 6 | coverage owned | the Sarvatobhadra half of the §5 Kāla row — state **unavailable**, with reason |
| 7 | position + baseline | root (0 dependencies); deployed 0 rows · current code = deployed · **risk 0** |
| 8 | disposition | **Q — qualify/limit authority.** Keep the abstention and keep it visible |
| 9 | fidelity | **PASS by abstention** — nothing inauthentic, unsourced or wrongly identified is stored, because nothing is stored |
| 10 | synergistic | none today; one populated `school_tag` row activates the consumer's DB path with no code change |
| 11 | cross-layer | 1 declared consumer (`ka_vedha_gochara`), which falls through to `l1_sarvatobhadra_vedha` (also empty) and then to a disclosed algorithmic approximation carrying `uncited_extension=true` |
| 12 | **preserved kernel** | the table, its `UNIQUE (school_tag, cell_kind, cell_index, table_version)` key, the `native_confirmed` column, and **the abstention itself** |
| 13 | **concepts + carriage check** | it would assert a classical grid → **D1 source correspondence**, which is exactly why it is empty: there is no passage to correspond to. Until a passage exists the check is *inapplicable*, not failed. *Chosen here — C-9.* |

### 0.2 · What it is for
It is the place a school's Sarvatobhadra grid will sit, keyed so several schools can sit side by side. Its
current value is negative space: it prevents one tradition's grid being seated as *the* classical grid,
which would be a school-selecting interpretive act disguised as an L0 base fact.

## §1 · Measured current state

- **Storage:** `bg_sarvatobhadra_grid` — **0 rows**, floor **0**, Δ 0. 10 columns: `school_tag`,
  `cell_index`, `cell_kind` (CHECK: `nakshatra_position` | `vedha_pair`), `cell_value`, `source_text_id`,
  `source_citation`, `table_version`, `native_confirmed` (default false), plus `id`/`created_at`.
  Migration 529 applied (ledger confirms one row).
- **Producer:** none — `has_writer` false, table created by migration, throughput sentinel marks it `lit`
  so the orchestrator does not treat 0 rows as an unbuilt asset.
- **Consumers:** 1 declared (`ka_vedha_gochara`, Kāla), which queries this table **first**.
- **Served surface:** **0 capability modules** — it is consumed by a writer, not exposed to a caller.
- **Build state:** `state=lit, rows_written=0, last_built_at=2026-08-09` — and here `rows_written=0` is
  **exactly true**, which is the contrast with pilot 4: the same value is honest here and ambiguous there.
- **Three-way baseline:** deployed 0 · current code 0 · target: 28 `nakshatra_position` rows + the
  passage's vedha pairs, under `school_tag='muhurta_chintamani'` (native decision 12). **Risk 0.**
- **Evidence state:** source-present ✗ (deliberately) · qualified N/A · consumed ✗ · served ✗ ·
  value-evaluated ✗. **Five of six states honestly negative, by design.**

### 1.1 · Completeness — width and depth
**Width 0 of a universe that is declarable and undeclared-by-necessity:** 28 nakshatra positions plus the
pairs a specific school's passage states — a number nobody can state until the passage is in hand. Depth:
the ten columns exist; none is populated. **This is the one asset in the pilot where 0% completeness is the
correct reading**, because the alternative is a transcribed guess.

### 1.2 · Reachability
0 of 0 — nothing built, nothing to reach. Not a shortfall.

## §3 · Obligations specialised

| obligation | satisfied means | detector |
|---|---|---|
| Source and domain fidelity | no row exists without a verse-level citation and a `school_tag` | the table is empty, so **satisfied vacuously and verifiably**: `count(*) WHERE source_citation IS NULL` = 0 of 0 |
| Operational honesty | the emptiness is declared as intentional everywhere it shows: registry floor 0, throughput 0, and a consumer that falls through and discloses `uncited_extension` | **PASS** — all three agree |

## §4 · The eight gates

| gate | verdict | reason |
|---|---|---|
| **Ldgr** | **N/A** | no rows to cite a source |
| **Idem** | **N/A** | no writer; nothing to replace or accrete |
| **Earn** | **PASS** | the rare case where every status surface tells the same true story: floor 0, `rows_written` 0, consumer discloses its fallback. Nothing claims a grid exists. |
| **Null** | **PASS** | the whole asset is an honest null — an empty school-keyed table stating that variants exist and none is held, instead of one seated silently |
| **Vocab** | **N/A** | emits no names. When seated, `cell_value` must carry ontology `nakshatra` ids and `school_tag` a `school` id — recorded now so the future gate is not re-derived |
| **Carr** | **N/A — inapplicable, not failed** | D1 is the applicable check and there is no passage to check against. The distinction matters: `NO_DETECTOR` would imply a claim nobody verifies; here there is no claim. |
| **Narr** | **N/A** | no prose |
| **Dens** | **N/A** | reaches no served surface |

## §5 · Ledger rows (registered)
`G01` the universe cannot be declared until the passage exists (blocked, not open work) ·
`G02` when seated, `cell_value`/`school_tag` must be ontology-resolved — a pre-registered future gate.

## §9 · Opportunity register

| id | dimension | what it would add | proposal | proof afterward |
|---|---|---|---|---|
| `O1` | **completeness** | activates a waiting consumer with no code change, and converts a disclosed approximation into a cited classical grid | seat the Muhūrta Cintāmaṇi grid per decision 12, once the chapter is ingested. **Blocked on one input, not on effort** — the full step list is the companion seating brief | `ka_vedha_gochara` takes the DB-grid path; `uncited_extension` no longer set for the grid term; every row carries a verse-level citation |
| `O2` | **architecture** | a second school beside the first, which is what the key was designed for | after O1, seat a second `school_tag` and let `kala_paddhati_profile` select — holding two grids is not preferring either | two schools resolvable; a profile switch changes the vedha reading and nothing else |

## §6 · Change packet — not authorised here
```
may_touch:      nothing yet — blocked on the Muhurta Chintamani chapter (companion seating brief)
must_not_touch: the abstention, without a native ruling · any applied migration
base:           5973d0132
```
Preserved kernel: the abstention, the key, and `native_confirmed` — the column that keeps "sourced" and
"confirmed" from collapsing into one claim.

## §2 · Shape
identity ✓ inputs/DAG ✓ correctness ✓ data sufficiency ✓ consumers ✓ value/target ✓ synergy ✓
knowledge-time ✓ change packet ✓ evidence ✓

## §7 · Certification — none (pilot)
## §8 · Review — unsigned. **Derivability: 13 of 13 — the only brief in the pilot with no invention, because row 13's carriage check is inapplicable here and the instance's silence cost nothing. Plus one template result: `N/A — inapplicable` and `NO_DETECTOR` are genuinely different verdicts, and this asset is the case that proves it.**
