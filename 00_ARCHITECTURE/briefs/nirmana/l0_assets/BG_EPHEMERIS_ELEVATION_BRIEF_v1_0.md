---
artifact: BG_EPHEMERIS_ELEVATION_BRIEF
canonical_id: BG_EPHEMERIS_ELEVATION_BRIEF
tier: 4
kind: instance
version: "1.0"
status: PILOT_DRAFT
produced_on: 2026-09-26
template: 00_ARCHITECTURE/briefs/nirmana/ASSET_ELEVATION_TEMPLATE_v2_0.md
layer_instance: 00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v3_0.md
pilot: yes
role_in_pilot: "3 of 5 — computed substrate. Stresses Carr D3, computational correctness, and the build-cost baseline."
measured_on: 2026-09-26
measured_against: "live asset_registry · production ephemeris_daily (read-only) · writers/bg_ephemeris.py and brahmagyan/l0_ephemeris.py at 5973d0132 · asset_throughput"
verdict: NONE
---

# bg_ephemeris — asset elevation brief (pilot 3 of 5)

**Headline: the grid is provably complete and the vocabulary is provably wrong.** 91,676 days × 9 bodies =
**825,084 rows exactly** — no missing cell, verified arithmetically. And `body` is stored as `'Jupiter'`
while the ontology's canonical id is `jupiter`: the largest table in L0 joins to the identity authority
only through an undeclared case normalisation, and the integrity check *pins* the capitalised form.

## §0 · Identity and inheritance

```
asset_id: bg_ephemeris · layer: L0 Brahmagyan · pilot: yes
kind: data (computed substrate) · scoring_mode: fidelity · role: neither
measured_on: 2026-09-26
```

### 0.1 · Inherited — thirteen rows

| # | what | value |
|---|---|---|
| 1 | P/V | **P21** (day/period in its proper context), **P13** (convention sensitivity); indirectly every timing P — V02, V04, V05, V13 |
| 2 | obligations | **computational correctness** (primary here — it computes, it does not testify) · source and domain fidelity · operational honesty |
| 3 | correctness + switch | no per-subject rows (PASS structurally); switch-irrelevant |
| 4 | presentation fields | the §3.4 row "conventions in force" — `ayanamsha_id`, `node_mode`, `epoch_convention` are carried **as data**, which is exactly what that row demands |
| 5 | contracts | **produces DP01's convention half and the positional substrate every clock reads**; consumes none |
| 6 | coverage owned | the astronomical substrate of the §5 Kāla row |
| 7 | position + baseline | root (0 dependencies); deployed 825,084 · current code = deployed · **risk 0** |
| 8 | disposition | **P — preserve**, with one E item (the body vocabulary) |
| 9 | fidelity | depth and width **PASS**; identity **FAIL** (case) |
| 10 | synergistic | nothing joins to it by identity today; its consumers key on the capitalised label |
| 11 | cross-layer | read in **71 files** — the most-read table in L0; evidence state **served** (4 modules) |
| 12 | **preserved kernel** | all 825,084 rows; the 1900–2150 span; the 9-body set; `ON CONFLICT (date, body, ayanamsha_id)`; the conventions-as-data columns |
| 13 | **concepts + carriage check** | it asserts a computed astronomical quantity → **D3 independent re-derivation**. D1 N/A (no classical passage to restate). D2 N/A. *Chosen here — layer defect C-9.* |

### 0.2 · What it is for
It is the sky, precomputed: for every day from 1900 to 2150, every classical body's longitude, speed,
retrogradation, sign and nakshatra. Without it every transit, every daśā boundary check and every
pañcāṅga would recompute ephemeris on demand, and no two answers would be guaranteed to agree.

## §1 · Measured current state

- **Storage:** `ephemeris_daily` — **825,084 rows** (own `count_sql`), floor 825,084, **Δ 0**. 15 columns.
- **Producer:** `writers/bg_ephemeris.py` (`@register("bg_ephemeris")`) → `brahmagyan/l0_ephemeris.py`;
  COPY into a temp table then `INSERT ... ON CONFLICT (date, body, ayanamsha_id) DO NOTHING` (L508).
- **Consumers:** **71 files** — the most-read L0 table. Registry declares 5 edges (all Kāla).
- **Served surface:** 4 capability modules reference it; **none declares a `density_contract`**.
- **Three-way baseline:** deployed = current code · **risk 0**.
- **Build cost: NOT INSTRUMENTED.** `asset_throughput`: `state=lit, rows_written=0, rows_per_second=NULL,
  last_built_at=2026-09-04` — zero rows recorded for the largest table in the layer.
- **Evidence state:** source-present ✓ qualified ✓ consumed ✓ transformed ✓ served ✓ · value-evaluated ✗.

### 1.1 · Completeness — width and depth

**Width: PASS on both axes, and provably.** `min(date)` 1900-01-01, `max(date)` 2150-12-31 →
**91,676 distinct days**, which is exactly 251 years × 365 + 61 leap days. Bodies: **9** — Sun, Moon,
Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu: the classical set, complete. **91,676 × 9 = 825,084 =
the row count**, so there is no missing (day, body) cell anywhere in 251 years. This is the cleanest
completeness result in the pilot, and it is arithmetic rather than assertion.

**Depth: complete.** Zero nulls in `tropical_longitude`, `speed_dps`, `nakshatra_number`,
`source_citation` across all 825,084 rows.

**The convention axis is declared and single-valued.** `ayanamsha_id` = 1 distinct value (`tropical` —
correct: longitudes are tropical and ayanāṃśa is applied downstream). `epoch_convention` = `noon_ut`.
`node_mode` = **`true` only** — mean-node positions are not held. The data plane warns explicitly that
"canonicalizing a node label must not erase true/mean-node conventions"; here the schema *can* express
both and holds one. That is a legitimate choice and an **undeclared** one: P13 asks what changes under
another convention, and for the node the answer cannot be computed from this table.

### 1.2 · Reachability
4 capability modules expose it. **Field-level census NOT MEASURED** this pass (recorded, not assumed).
Row-level: reachable by date and body through the served modules; no enumeration of 825,084 rows is
expected or needed. Requirement **[TRANSFERS]**.

## §3 · Obligations specialised

| obligation | satisfied means | detector |
|---|---|---|
| Computational correctness | a position reproduces when derived a second way from different inputs | D3 — **does not exist** (G02) |
| Source and domain fidelity | the conventions in force are carried with every row | **PASS** — three convention columns, no nulls |
| Operational honesty | the build record carries a real figure for the layer's largest table | `rows_written` non-zero (G03) |

## §4 · The eight gates

| gate | verdict | detector and evidence |
|---|---|---|
| **Ldgr** | **PASS** | `source_citation` on 825,084/825,084 rows |
| **Idem** | **PASS** | `ON CONFLICT (date, body, ayanamsha_id) DO NOTHING` (L508) — L0 upsert convention |
| **Earn** | **PARTIAL** | `integrity_check_sql` is a real detector that can fail — it asserts the exact row count, span, body set and `ayanamsha_id='tropical'`. But `asset_throughput.rows_written = 0` against 825,084 rows is a status with no measurement behind it (G03). |
| **Null** | **PASS** | no content nulls anywhere |
| **Vocab** | **FAIL** | rules 1–3 apply. `body` is stored as `'Jupiter'`, `'Ketu'`, `'Mars'`… while `brahma_ontology`'s `planet` canonical ids are `jupiter`, `ketu`, `mars`. Every join from the sky to the identity authority passes through an **undeclared case normalisation** — rule 3's exact defect, in the most-read table in the layer. Worse, the `integrity_check_sql` **pins the capitalised array**, so the vocabulary fix and the integrity check must move together. |
| **Carr** | **NO_DETECTOR** | D3 is the applicable check. The integrity check verifies *shape* (count, span, body set) and never recomputes a single position from different inputs. 825,084 computed values, none independently re-derived. |
| **Narr** | **N/A** | emits no prose |
| **Dens** | **FAIL** | 4 serving modules, 0 `density_contract` declarations |

## §5 · Ledger rows (registered)
`G01` body-case vocabulary (+ the integrity check pin) · `G02` no D3 re-derivation · `G03` build record
reads 0 rows · `G04` node_mode single-valued and undeclared · `G05` no density contract on 4 modules ·
`G06` field-level reachability not measured. Opportunities `O1`–`O4` in §9.

## §9 · Opportunity register

| id | dimension | what it would add / remove | proposal | proof afterward |
|---|---|---|---|---|
| `O1` | **architecture** | answers P13 for the node convention, which today cannot be answered from this table | add `node_mode='mean'` rows, or declare in the release that only the true node is held and that a mean-node question is `unavailable`. Input delta: same ephemeris source, one more pass. Output delta: better (a convention comparison becomes computable). Build-cost delta: +825,084 rows ≈ 2× the table. | a mean-vs-true comparison returns two answers where it returns one today; row count doubles as predicted |
| `O2` | **architecture / build cost** | the grain question, taken deliberately once | 825,084 rows is **daily** granularity; intraday positions must be interpolated or recomputed by consumers. Options: keep daily and declare interpolation the consumer's job; store speed-based interpolation coefficients; or move to on-demand Swiss computation with a cache. Each changes cost and precision in opposite directions. | positional error against a Swiss recomputation at sub-daily times, before and after; cost per query and per rebuild |
| `O3` | **algorithm** | a real second opinion on 825,084 computed values | build **D3**: recompute a sample of positions a second way (different epoch handling or a second library) and compare within a declared tolerance; seed one deliberate error to prove the check fails. | the detector reports a non-zero mismatch on the seeded case and zero on the corpus |
| `O4` | **build cost** | a baseline where none exists for the layer's largest build | instrument the COPY path: rows and duration to `asset_throughput` | the record carries a rate; O2's cost options become comparable against a real number |

## §6 · Change packet — not authorised here
```
may_touch:      platform/python-sidecar/brahmagyan/l0_ephemeris.py · the bg_ephemeris integrity_check_sql (migration) · 4 capability modules
must_not_touch: pipeline/orchestrator/** · any applied migration · the 825,084 existing rows' values
base:           5973d0132
```
Preserved kernel: every row and every convention column; the span; the 9-body set; the upsert key.
**The body-case fix is not a data edit**: it is a vocabulary decision (normalise at the authority per
pilot 1's O1, or rename the column's values and update the integrity check in one migration) and it
touches 71 files' worth of readers. Rollback: the integrity check is the guard — it fails loudly if the
body set changes unexpectedly.

## §2 · Shape
identity ✓ inputs/DAG ✓ correctness ✓ data sufficiency ✓ consumers ✓ value/target ✓ synergy ✓
knowledge-time ✓ (`date` is the axis; no `as_of`) change packet ✓ evidence ✓

## §7 · Certification — none (pilot)
## §8 · Review — unsigned. **Derivability: 12 of 13; row 13 chosen (C-9, third confirmation).**
