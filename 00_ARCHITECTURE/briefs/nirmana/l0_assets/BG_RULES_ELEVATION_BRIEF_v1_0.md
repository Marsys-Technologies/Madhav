---
artifact: BG_RULES_ELEVATION_BRIEF
canonical_id: BG_RULES_ELEVATION_BRIEF
tier: 4
kind: instance
version: "1.0"
status: PILOT_DRAFT
produced_on: 2026-09-26
template: 00_ARCHITECTURE/briefs/nirmana/ASSET_ELEVATION_TEMPLATE_v2_0.md
layer_instance: 00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v3_0.md
pilot: yes
role_in_pilot: "2 of 5 — a rule corpus. Stresses Carr D1, the width census, and the §9 algorithm row."
measured_on: 2026-09-26
measured_against: "live asset_registry · production sutravali_rules and classical_text_chunks (read-only) · writers/bg_rules.py and brahmagyan/l0_sutravali_extractor.py at 5973d0132 · asset_throughput"
verdict: NONE
---

# bg_rules — asset elevation brief (pilot 2 of 5)

**Headline: the extractor's yield varies 29× across texts, and the foundational text is near the bottom.**
BPHS holds 1,459 corpus chunks and yields 112 rules (0.08 per chunk); Sāravalī holds 471 and yields 1,101
(2.34). One text, Tājaka Nīlakaṇṭhī, holds 290 chunks and yields **zero**. The corpus is not being
extracted; the two texts whose formatting the regex happens to match are.

## §0 · Identity and inheritance

```
asset_id: bg_rules · layer: L0 Brahmagyan · pilot: yes
kind: data · scoring_mode: fidelity · role: neither (it supplies the warrant both rest on)
measured_on: 2026-09-26 · measured_against: registry · production · code at 5973d0132
```

### 0.1 · Inherited — thirteen rows

| # | what | value |
|---|---|---|
| 1 | P/V | **P15** (what supports this, where schools disagree) and **P22** (the texts) directly; **P09** (yoga prerequisites), **P20** (method scope); **V08** source learning |
| 2 | obligations | source and domain fidelity (primary) · operational honesty · delivery fidelity |
| 3 | correctness + switch | no per-subject rows (PASS structurally); switch-irrelevant; no invented rule or source |
| 4 | presentation fields | the §3.4 row "method and school a finding rests on, and where authorities disagree" — this asset carries the *rule clause* half |
| 5 | contracts | **produces DP02 rule qualification** to L1 formation, L2 interpretation, L3 activation, investigator. Consumes none |
| 6 | coverage owned | the *qualified-rule* half of the §5 rows — 3,002 rules over 14 texts |
| 7 | position + baseline | depth 1 (depends on bg_texts, bg_yogas, bg_dasha_systems); deployed 3,002 · current code = deployed · risk 0 |
| 8 | disposition | **E — enrich/correct** (the concept link and the extraction yield) |
| 9 | fidelity | source presence **PASS**; linkage **WEAK**; see §4 |
| 10 | synergistic | it is the left-hand side of **seam B (rules → concepts)** — the layer's weakest seam, 17 of 3,002 |
| 11 | cross-layer | DP02, read in 29 files; evidence state **served** (MCP surface only, §1.2) |
| 12 | **preserved kernel** | the 3,002 extracted rules with their `text_id` + `verse_ref` provenance; the deterministic extractor `python_regex_v2`; `ON CONFLICT DO NOTHING` |
| 13 | **concepts + carriage check** | every rule asserts a classical claim attributed to a verse → **D1 source correspondence**. D2 N/A (one rule, one witness). D3 N/A (nothing computed). *Chosen here, not inherited — layer defect C-9.* |

### 0.2 · What it is for
It converts read text into applicable rules: for each claim, the antecedent that must hold, the predicate,
the prediction, and the verse it rests on. Without it the corpus is readable and nothing in it is
*applicable* — every later layer would have to re-derive doctrine from prose at query time.

## §1 · Measured current state

- **Storage:** `sutravali_rules` — **3,002 rows** (own `count_sql`), floor 3,002, **Δ 0**. 14 columns.
- **Producer:** `writers/bg_rules.py` → `brahmagyan/l0_sutravali_extractor.py`; `ON CONFLICT DO NOTHING`
  (L1463, L1505) — the L0 upsert convention. Extractor: **one**, `python_regex_v2`, deterministic (§N.4).
- **Consumers:** 29 files repo-wide; registry declares 2 edges (Bodha, Mīmāṃsā).
- **Served surface — and it is a split one:** exposed through the **MCP tool surface**
  (`platform-mcp/src/tools/l0_brahmagyan.ts`, `ref_rules_search`), and **absent from all 46 L0
  retrieval-registry capability modules**. A caller on the retrieval registry cannot reach 3,002 rules.
- **Three-way baseline:** deployed 3,002 · current code identical · **risk 0**.
- **Build cost: INSTRUMENTED, partially.** `asset_throughput`: `state=lit, rows_written=3002,
  rows_per_second=NULL, last_built_at=2026-09-06`. Row count real (contrast `bg_ontology`'s 0); **no
  duration or rate**, so no cost baseline to beat.
- **Evidence state:** source-present ✓ qualified ✓ consumed ✓ transformed ✓ served ✓ (one surface) ·
  value-evaluated ✗.

### 1.1 · Completeness — width and depth

**Depth: 9 of 12 content dimensions complete.** `text_id`, `verse_ref`, `antecedent_jsonb`,
`predicate_jsonb`, `prediction_jsonb`, `confidence`, `quality_score`, `extracted_by`, `transit_marker` —
all **3,002 / 3,002**. Failing: `yoga_canonical_id` **17 / 3,002 (0.6%)** · `dasha_system_id`
**0 / 3,002 (0%)** — a column that has never been populated.

**Width: measured against the corpus, and it is the finding.** The universe is undeclared (nothing says
how many rules a text contains), so the measurable proxy is yield per chunk:

| text | chunks | rules | rules/chunk |
|---|---|---|---|
| saravali | 471 | 1,101 | **2.34** |
| bhrigu_nandi_nadi | 608 | 982 | 1.62 |
| hora_sara | 460 | 176 | 0.38 |
| jataka_parijata | 704 | 164 | 0.23 |
| brihat_jataka · yavana_jataka · phaladeepika | 607 · 1,298 · 564 | 100 · 190 · 82 | 0.16 · 0.15 · 0.15 |
| **bphs** | **1,459** | **112** | **0.08** |
| uttara_kalamrita · sarvartha_chintamani · bphs_jaimini | 289 · 342 · 264 | 16 · 16 · 11 | 0.06 · 0.05 · 0.04 |
| brihat_samhita · nadi_navamsa_patel · muhurta_chintamani | 1,171 · 1,850 · 274 | 25 · 23 · 4 | 0.02 · 0.01 · 0.01 |
| **tajaka_neelakanthi** | **290** | **0** | **0.00** |

- **14 of 15 corpus texts yield rules; Tājaka Nīlakaṇṭhī yields none** from 290 chunks.
- **29× spread** between the best and the worst non-zero text. At Sāravalī's rate BPHS alone would yield
  ~3,400 rules — more than the entire corpus holds today.
- Two rule texts are not in the ontology's `text` class (`bhrigu_nandi_nadi`, `bphs_jaimini`) — the same
  defect surfaced in pilot 1's width census.

### 1.2 · Reachability

- **Rows:** reachable only by **search** through `ref_rules_search`; no enumeration path measured, and no
  retrieval-registry capability at all. Rows reachable through the retrieval registry: **0 of 3,002**.
- **Fields: NOT MEASURED** this pass — the MCP tool's projection was not censused. Recorded as a gap, not
  assumed complete.
- Requirement **[TRANSFERS]** to the retrieval plane; the measurement is here.

## §3 · Obligations specialised

| obligation | satisfied means | detector |
|---|---|---|
| Source and domain fidelity | each rule's antecedent/predicate/prediction matches the verse it cites | D1 — **does not exist** (G03) |
| Operational honesty | `confidence` means something a reader can act on; the build record carries a rate | the distribution check (G02); `rows_per_second` non-null |
| Delivery fidelity | a caller can reach the rules from the retrieval registry, not only the MCP surface | the §1.2 census (G05) |

## §4 · The eight gates

| gate | verdict | detector and evidence |
|---|---|---|
| **Ldgr** | **PASS** | root-layer reading: 3,002/3,002 carry `text_id` + `verse_ref`; 14 distinct texts |
| **Idem** | **PASS** | `ON CONFLICT DO NOTHING` in the extractor (L1463, L1505) — L0 upsert convention |
| **Earn** | **FAIL** | `confidence` has **3 distinct values** (0.600, 0.800, 1.000) across 3,002 rows, 2,770 of them 1.000 — a 3-level tier presented as a continuous score. And **`confidence = quality_score` on 3,002 of 3,002 rows**: two columns, one signal. A consumer treating either as a graded confidence is reading a constant for 92% of the corpus. |
| **Null** | **PASS** | no content column is null anywhere; `dasha_system_id` is uniformly null, which is honest (never populated) rather than defaulted |
| **Vocab** | **PARTIAL** | rules 1–3 apply. `yoga_canonical_id` resolves to the ontology where present (17 rows). `text_id` uses the corpus vocabulary, of which **2 of 14 values have no ontology identity**. Rule 3: the same undeclared-normalisation defect as pilot 1. |
| **Carr** | **NO_DETECTOR** | D1 is the applicable check and nothing compares a rule to its verse. This is the asset where D1 matters most — 3,002 encoded claims, none verified against its source. |
| **Narr** | **N/A** | `prediction_jsonb` carries structured fields, not narration re-derived over computed facts. In D1's scope once that detector exists. |
| **Dens** | **FAIL** | reaches a served surface (MCP) with no `density_contract`; and 0 of 46 retrieval-registry modules expose it |

## §5 · Ledger rows (registered)

`G01` yield · `G02` confidence/quality collapse · `G03` no D1 · `G04` concept link 17/3,002 ·
`G05` retrieval-registry absence · `G06` dasha_system_id never populated · `G07` tajaka zero yield ·
`G08` two text_ids with no ontology identity. Opportunities `O1`–`O4` in §9.

## §9 · Opportunity register

| id | dimension | what it would add | proposal | proof afterward |
|---|---|---|---|---|
| `O1` | **algorithm** | the corpus actually extracted — potentially several thousand additional qualified rules, which is the largest single value increase available anywhere in L0 | `python_regex_v2` is one regex family applied to fifteen differently-formatted texts. Replace with **per-text structure-aware extraction**: normalise chunk shape per text (verse numbering, sloka boundaries, translator conventions) before extraction, and keep the extractor deterministic. **Not an LLM extractor** — §N.4 deterministic-first. Input delta: same corpus. Output delta: elevated. Build-cost delta: higher per run, once. | rules/chunk per text before and after; **and** D1 correspondence on a sample of the new rules, so yield is not bought with precision |
| `O2` | **algorithm** | one honest signal instead of two identical ones | collapse `confidence` and `quality_score` (identical on 3,002/3,002) into one field whose vocabulary is the three tiers it actually has, or make one of them measure something different | the distribution: one field, three named tiers, and a consumer reading a tier rather than a false continuum |
| `O3` | **synergy** | seam B, provable | 17 of 3,002 rules link to a concept. A rule that names the concept it qualifies lets L2 find the doctrine behind a structural claim without re-parsing prose. Link via the ontology's declared key — which O1 of pilot 1 settles | seam-B ablation: break the concept link and measure the served reading; today the seam is too thin to break |
| `O4` | **build cost** | a real baseline | `rows_written` is real; `rows_per_second` and duration are null. Instrument the extractor's run | the record carries a rate; O1's cost delta becomes measurable against it |

## §6 · Change packet — not authorised here
```
may_touch:      platform/python-sidecar/brahmagyan/l0_sutravali_extractor.py · a new D1 detector · retrieval-registry capability for rules
must_not_touch: pipeline/orchestrator/** · the corpus tables (bg_texts' own brief) · any applied migration
base:           5973d0132
```
Preserved kernel: the 3,002 rules and their verse provenance; the deterministic extractor; the upsert key.
Writer conformance: conformant. Migration: only if the confidence/quality collapse needs a column change.
Rollback: re-extract. Consumer impact: 29 files; a yield increase changes row counts downstream — the
floor is aspirational and must be re-stamped, not defended.

## §2 · Shape
identity ✓ inputs/DAG ✓ correctness ✓ data sufficiency ✓ consumers ✓ value/target ✓ synergy ✓
knowledge-time ✓ (no `as_of`) change packet ✓ evidence ✓

## §7 · Certification — none (pilot)
## §8 · Review — unsigned. **Derivability: 12 of 13 rows; row 13 chosen, layer defect C-9 (second confirmation).**
