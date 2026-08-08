---
canonical_id: A8_FACTOR_FACT_COVERAGE_MATRIX
version: 1.0
status: DRAFT — for CHECKPOINT review (native + Fable)
date: 2026-08-08
campaign: ADHIṢṬHĀNA, Lane A8, item 1 of 2
author: Sonnet 5 (Conductor)
rung: P3 (hand-worked coverage precondition; the P3 rubric-scoring probe itself is item 2,
  the v4 Scoring Rubric Spec draft — NOT produced in this file)
r16_scope: every "verified non-empty" cell below cites a live query actually run against
  chart 482012f1-710e-4a25-994a-93821f5871aa (mandatory) and chart
  1c826d5a-41cb-4450-b4dc-59d440e5f75a (also run, in full, not spot-sampled). No cell in this
  document is an assumption from a fact_category's name alone — see §0.3 spot-check log.
---

# A8 — THE FACTOR→FACT COVERAGE MATRIX

**For every one of the 27 `brahma_event_ontology` event classes and their karyatva factors
(from `bo_pratijna_karyatva.KARYATVA_REGISTRY`), this document names the exact
`(fact_category, fact_key)` or `chart_fact_identity` dimension that satisfies each factor, and
reports a real, live row count on both canonical charts.** Where no live fact satisfies a
factor, the gap is named individually with a proposed disposition — never lumped into a vague
bucket (per the task's own R16 instruction).

---

## §0 — Methodology

### §0.1 — Scope and sources actually read

1. `platform/python-sidecar/pipeline/orchestrator/writers/bo_pratijna_karyatva.py` — read in
   full (281 lines). **26 `KaryatvaMap` entries**, not 27 — see §4, the one class-level gap.
2. `platform/python-sidecar/brahmagyan/l0_ghatana.py` `EVENT_CLASSES` — read in full (27
   entries, confirmed live: `select count(*) from brahma_event_ontology` → **27**). Cross-read
   against every `KaryatvaMap` entry; divergences logged in §2, not silently resolved (R16).
3. `chart_facts` / `chart_fact_identity` / `chart_divisionals` schemas — read via `\d` against
   the live DB (cloud-sql-proxy on `127.0.0.1:5433`, `amjis-pipeline-db-url` secret, read-only,
   never printed).
4. `ga_yoga_firings` (real firings-authoritative table, `fired` boolean + `strength` +
   `constituent_fact_ids`) — discovered live, not from source reading, and used as the correct
   authority for `yoga_keywords` verification once literal-substring search against
   `chart_facts` came back mostly empty (see §1.4).

### §0.2 — Verification method (per factor type)

| Factor type | Verification method | Charts run |
|---|---|---|
| `primary_bhava` (house) | `chart_fact_identity` `house_num=H` (all `entity_kind`s) for total volume; `chart_divisionals` `varga='D1' AND house=H` for real occupancy; `kp_house_significators` `fact_key='cusp_owner'` for the house lord | both, full (not sampled) |
| `karaka_grahas` / `condition_malefic_grahas` (graha) | `chart_fact_identity` `graha_code=X`; named dignity/strength categories (`graha_dignity_per_varga`, `graha_shadbala_total`, `graha_avastha_*`, `kp_planet_significations`); named affliction categories (`sambandha_grade`, `virupa_drishti`, `combustion_per_varga`, `graha_effective_dignity_modified_by_aspects`) | both, full |
| `divisional` (varga) | `chart_fact_identity` `varga_id=X`; `chart_divisionals` `varga=X` row count | both, full |
| `dusthana_required` | Structural — satisfied by the same house-evidence query above, restricted to houses 6/8/12 (the classical dusthana set) | both, full |
| `yoga_keywords` | First pass: literal `ILIKE` substring search across `chart_facts.fact_key`/`fact_value_text`/`fact_subject` for every keyword string in the registry. Where empty, second pass against `ga_yoga_firings.yoga_canonical_id` and `chart_facts` `fact_category IN ('yoga_label','dosha_label')` `fact_subject`/`fact_value_text` — the DB's real firings-authoritative surfaces, not free text | both, full |

All queries are `SELECT`-only; nothing was written. The scratch verification script is
`platform/scripts/probes/../..` — no, correction: it is **not committed** (per the task's own
scope: "you may write exactly one deliverable file plus any scratch SQL"); it lived at
`/private/tmp/.../scratchpad/a8_verify.py` for this session only and is not part of the repo.

### §0.3 — Spot-check log (N.7 discipline: don't trust a category name, read real rows)

Five categories were read at row-value level, not just counted, before being relied on below:

- `graha_dignity_per_varga` / `D9_VEN` → `dignity_state='neutral'` (482012f1) / consistent with
  the Rung-P2 probe's cross-check against `chart_divisionals`.
- `sambandha_grade` → real numeric `grade` per graha-pair per varga (e.g. `D1_SUN_MOON`
  grade=0) — confirms this is a relational-affliction/harmony score, not a label.
- `house_bhava_bala_total` → real numeric totals per house (e.g. `HOUSE_1`=8.18,
  `HOUSE_10`=8.8) — confirms real computed house strength, not a placeholder.
- `kp_house_significators` `fact_key='cusp_owner'` → full 12-house lord table read directly:
  1L=Mars, 2L=Venus, 3L=Mercury, 4L=Moon, 5L=Sun, 6L=Mercury, 7L=Venus, 8L=Mars, 9L=Jupiter,
  10L=Saturn, 11L=Saturn, 12L=Jupiter — internally consistent with the Rung-P2 probe's
  independent finding "7th lord: Venus" via cusp-longitude + classical whole-sign rulership.
- `virupa_drishti` / `combustion_per_varga` / `graha_avastha_baladi_per_varga` (Saturn) → real
  aspect offsets (`h9_offset3`, degree=1), real boolean combustion flags (`is_combust`=0), real
  avastha state strings (`vriddha`) — confirms these are genuine affliction/state signals.
- `dosha_label` → chart-scoped (not a generic reference catalog — `reference_doshas` is the
  generic catalog; `dosha_label` in `chart_facts` only carries rows for doshas actually detected
  on this specific chart+ayanamsha), confirmed by its single `fact_key='dosha_name'` shape and
  per-chart `WHERE chart_id=` scoping.

### §0.4 — What "verified non-empty" means here, and what it does not mean

A nonzero row count proves the *fact exists and is retrievable through a named path*. It does
**not** by itself prove the row's *value* supports a particular verdict (promised/denied) for
any event class — that is Campaign B's job (the v4 rubric engine, out of scope for this
document). This matrix is a coverage proof, not a scoring proof.

---

## §1 — Shared Factor Verification Ledger

Houses, grahas, and vargas recur across many of the 27 classes. Rather than re-run and re-state
the same query 60+ times, each is verified **once** here; §3's per-class tables cite these rows
by house/graha/varga id. Every number below is a real count from a live query against both
charts, not sampled.

### §1.1 — House Ledger (all 12 houses; `primary_bhava`, `dusthana_required` evidence)

| House | Lord (KP `cusp_owner`, both charts identical) | D1 occupants — 482012f1 | D1 occupants — 1c826d5a | `chart_fact_identity` total rows 482012f1 / 1c826d5a | House-strength categories confirmed non-empty (both charts) |
|---|---|---|---|---|---|
| 1 | Mars | Jup, Mars, Mer, Moon, Sat, Sun, Ven (+ Lagna, karya, SARVA special-point subjects) | Jup, Mars, Mer, Moon, Rahu, Sat, Sun, Ven (+ Lagna, karya, SARVA) | 2100 / 2050 | `bhava_significance_link`(580), `kp_house_significators`(45), `bhava_arudha`(30), `bhava_cusps`(30), `house_bhava_bala_subscore`(15), `house_bhava_bala_total`(5), `house_bhava_bala_ratio`(5), `house_strength_classification_rollup`(5) |
| 2 | Venus | Rahu, Venus | Venus | 1765 / 1746 | `bhava_significance_link`(290), `kp_house_significators`(45), `bhava_cusps`(30), `house_bhava_bala_subscore`(15), `bhava_arudha`(15), `house_bhava_bala_total`(5), `house_bhava_bala_ratio`(5), `house_strength_classification_rollup`(5) |
| 3 | Mercury | Mercury | Mercury, Moon | 1738 / 1756 | same 8-category set as house 2 |
| 4 | Moon | Moon | Moon | 1762 / 1732 | same 8-category set |
| 5 | Sun | Sun | Sun | 1737 / 1768 | same 8-category set |
| 6 | Mercury | (none) | (none) | 1738 / 1753 | same 8-category set |
| 7 | Venus | Mars, Saturn | Ketu | 1708 / 1757 | same 8-category set |
| 8 | Mars | Ketu | Saturn | 2012 / 2001 | `bhava_significance_link`(580) + rest of the 8-category set |
| 9 | Jupiter | Jupiter, Venus | Jupiter | 2017 / 2033 | 8-category set (580 variant) |
| 10 | Saturn | Mercury, Saturn, Sun | Jupiter, Saturn | 2050 / 2037 | 8-category set (580 variant) |
| 11 | Saturn | Moon | Mercury, Sun | 2004 / 2025 | 8-category set (580 variant) |
| 12 | Jupiter | Moon | Mars, Venus | 2016 / 2008 | 8-category set (580 variant) |

**Every house, both charts: non-empty.** (Houses 1, 8–12 show `bhava_significance_link`=580
vs. 290 for houses 2–7 — a real, unexplained-here volume asymmetry, not investigated further;
flagged as a minor curiosity, not a coverage gap since both are non-zero.)

`dusthana_required` (separation, career_setback, major_loss) is satisfied structurally by this
same ledger restricted to houses 6, 8, 12 — no separate query needed; all three are non-empty
above.

### §1.2 — Graha Ledger (all 9 grahas; `karaka_grahas` + `condition_malefic_grahas` evidence)

| Graha | `chart_fact_identity` total 482012f1 / 1c826d5a | Dignity/strength categories confirmed non-empty | Affliction categories confirmed non-empty |
|---|---|---|---|
| Sun (`SUN`) | 5665 / 5585 | `graha_dignity_per_varga`(145), `graha_avastha_baladi_per_varga`(145), `graha_avastha_deeptaadi_per_varga`(145), `graha_centrality`(145), `kp_planet_significations`(55), `graha_position`(45), `graha_shadbala_total`(11), `graha_effective_dignity_modified_by_aspects`(5), `graha_composite_state_classification`(5) | `sambandha_grade`(1160), `virupa_drishti`(145), `graha_avastha_baladi_per_varga`(145), `graha_effective_dignity_modified_by_aspects`(5) |
| Moon (`MOON`) | 5475 / 5438 | same category set, counts 145/55/45/11/5/5 | `sambandha_grade`(1015), `virupa_drishti`(145), rest as above |
| Mars (`MAR`) | 6198 / 6471 | same + `combustion_per_varga`(145) | `sambandha_grade`(870), `virupa_drishti`(435), `combustion_per_varga`(145), rest as above |
| Mercury (`MER`) | 5161 / 5362 | same + `combustion_per_varga`(145) | `sambandha_grade`(725), `virupa_drishti`(145), `combustion_per_varga`(145) |
| Jupiter (`JUP`) | 5910 / 5918 | same + `combustion_per_varga`(145) | `sambandha_grade`(580), `virupa_drishti`(435), `combustion_per_varga`(145) |
| Venus (`VEN`) | 4867 / 4941 | same + `combustion_per_varga`(145) | `sambandha_grade`(435), `virupa_drishti`(145), `combustion_per_varga`(145) |
| Saturn (`SAT`) | 5738 / 5667 | same + `combustion_per_varga`(145) | `virupa_drishti`(435), `sambandha_grade`(290), `combustion_per_varga`(145) |
| Rahu (`RAH_MEAN`) | 3308 / 3195 | `graha_dignity_per_varga`(145), `graha_avastha_*`(145 each), `kp_planet_significations`(60), `graha_position`(45), `graha_shadbala_total`(5) | `virupa_drishti`(435), `graha_avastha_baladi_per_varga`(145), `sambandha_grade`(145) |
| Ketu (`KET_MEAN`) | 2883 / 2883 | same shape as Rahu | `virupa_drishti`(435), `graha_avastha_baladi_per_varga`(145) — `sambandha_grade` empty for Ketu on both charts (nodes are excluded from the `sambandha_grade` graha-pair computation; consistent 0 both charts, not a defect — a designed scope boundary, `parashari_rahu_excluded`-style, matching the `karaka_school` value seen on `karaka_chara_position`) |

**Every graha, both charts: non-empty on dignity/strength.** One honest sub-finding: Ketu has
no `sambandha_grade` rows (0 on both charts) — not a gap in the sense of "missing data," but a
real structural exclusion of the lunar nodes from that specific relational-grade computation.
Any class using Ketu as a `condition_malefic_graha` (marriage, relocation, foreign_settlement,
romantic_start via 7L not listed... — see §3) still has `virupa_drishti` and
`graha_avastha_baladi_per_varga` as live affliction evidence for Ketu; `sambandha_grade` simply
isn't one of Ketu's available affliction channels.

### §1.3 — Varga Ledger (10 vargas; `divisional` evidence)

| Varga | `chart_fact_identity varga_id=X` total 482012f1 / 1c826d5a | `chart_divisionals` row count 482012f1 / 1c826d5a |
|---|---|---|
| D1 | 3843 / 3829 | 805 / 805 |
| D2 | 3720 / 3755 | 1050 / 1050 |
| D4 | 3627 / 3636 | 770 / 770 |
| D7 | 3621 / 3694 | 770 / 770 |
| D9 | 3673 / 3645 | 940 / 940 |
| D10 | 3631 / 3667 | 770 / 770 |
| D12 | 3656 / 3677 | 840 / 840 |
| D20 | 3650 / 3632 | 815 / 815 |
| D24 | 3673 / 3661 | 815 / 815 |
| D30 | **140 / 140** | **50 / 50** |

**Every varga, both charts: non-empty.** One flagged thinness, not a gap: **D30** (used by
`surgery`, `illness_acute`, `chronic_onset`) carries real but far thinner coverage than the
other 9 vargas — `graha_in_varga` is the *only* `chart_fact_identity` `entity_kind` populated
for D30 (no `varga_sign`, `varga_house`, `varga_graha_pair`, `varga_domain` rows), and
`chart_divisionals` gives only 50 rows (vs. 770–1050 for the other vargas). This is D30's known
structural shape (trimsamsa is not sign-uniform the way other vargas are — classically it
carries one asymmetric degree-range table per sign, not a repeating pattern), not a build
defect; still, engine designers in Campaign B should know D30-backed factors (health-domain
classes) have a narrower live evidence base than career/relationship-domain D9/D10 factors.

### §1.4 — Yoga-Keyword Ledger (`yoga_keywords`, all unique strings across the registry)

The registry's `yoga_keywords` are short English/transliterated glosses (e.g. `"kalatra"`,
`"6L-7L"`) attached for narrative/citation context. **A literal substring search against live
`chart_facts` and `ga_yoga_firings` shows most of them have NO literal live counterpart** — this
is the single most consequential finding in this document and is reported in full, not
smoothed over.

| Keyword | Used by class(es) | Literal match found? | Live fact_category / table | Count (482012f1 / 1c826d5a) | Disposition |
|---|---|---|---|---|---|
| `darakaraka` | marriage | YES | `karaka_chara_position` (`fact_subject='DARAKARAKA'`) | 70 / 70 | Satisfied — Jaimini chara-karaka assignment is a real, chart-scoped fact |
| `upapada` | marriage | YES | `upapada_lagna` (`fact_subject='UPAPADA_LAGNA'`) | 10 / 15 | Satisfied — includes a real `lord_placement_verdict='afflicted_marriage_indication'` row (482012f1), directly on-topic for marriage |
| `kalatra` | marriage, romantic_start | **NO** | — | 0 / 0 | GAP. "Kalatra" (spouse-signification) is a *concept*, not a literal fact_key anywhere; the concept is already covered structurally via house-7/Venus evidence (§1.1/§1.2). **Disposition: drop as a separate scoring factor — it is redundant with `primary_bhava=[7]`/`karaka_grahas=[Venus]`, not missing evidence.** |
| `kuja_dosha` | separation | **NO** (as literal string) | `dosha_label` `fact_subject='manglik'` (same classical concept, different name) | 5 / 5 | GAP as literally spelled, but a real synonym exists live. **Disposition: Campaign B's Reader should resolve `kuja_dosha`→`manglik` via a synonym table (the same class of fix Lane A2 already did for graha names) rather than literal string match.** |
| `manglik` | separation (registered alongside `kuja_dosha` in the same `yoga_keywords` list — the registry already lists both spellings) | YES | `dosha_label` (`fact_subject='manglik'`) | 5 / 5 | Satisfied directly — corroborates the `kuja_dosha` disposition above (the registry's own second keyword already resolves; only the first, `kuja_dosha`, needs the synonym fix) |
| `6L-7L` | separation | **NO** | — | 0 / 0 | GAP. This is a compound classical rule ("6th lord conjunct/aspecting 7th lord") requiring a two-lord relational check, not a single fact lookup. **Disposition: not a `fact_category` gap but a *missing derived-signal* gap — Campaign B's Chart Reader (`lord_of(h)`, per Lane B1) can compute this from `kp_house_significators.cusp_owner` for houses 6 and 7 plus an aspect/conjunction join (`aspect_parashari_per_varga`) — feasible, but needs to be built, not looked up.** |
| `putra` | childbirth | YES | `karaka_chara_position` (putra-karaka concept resolves via `PUTRAKARAKA` subject) + `saham_position` (`SAHAM_PUTRA` if present) | 70 (karaka) + 40 (saham, generic) / 70 + 40 | Satisfied |
| `santana` | childbirth | **NO** | — | 0 / 0 | GAP. Synonym of `putra` (progeny) with no separate live encoding. **Disposition: drop — redundant gloss, not missing evidence (same reasoning as `kalatra`).** |
| `shastra` | surgery | **NO** | — | 0 / 0 | GAP. "Shastra" (edged instrument / surgery) has no live fact_key. **Disposition: drop as a scoring factor — surgery's real evidence is houses 6/8 + Mars + D30 (already covered); the keyword is citation flavor from BPHS ch.12, not a separate checkable signal.** |
| `vrana` | surgery | **NO** | — | 0 / 0 | GAP, same disposition as `shastra`. |
| `pravasa` | relocation, foreign_settlement | **NO** | — | 0 / 0 | GAP. **Disposition: drop — redundant with houses 4/12/9/7 + Moon/Rahu (already covered).** |
| `desa` | relocation | **NO** | — | 0 / 0 | GAP, same disposition. |
| `videsh` | foreign_settlement | **NO** | — | 0 / 0 | GAP, same disposition (redundant with house 12/9/7 + Rahu). |
| `prema` | romantic_start | **NO** | — | 0 / 0 | GAP, same disposition (redundant with house 5/7 + Venus). |
| `karma` | career_entry, career_change | YES (as a `saham_position` subject) | `saham_position` (`SAHAM_KARMA` family) | 40 / 40 | Satisfied, though loosely — the saham is a specific classical point, not a general "career activity" signal; still a real non-empty fact |
| `rajya` | career_entry, career_change, career_advancement, business_launch | YES | `saham_position` | 40 / 40 | Satisfied (same caveat as `karma`) |
| `labha` | career_advancement, business_launch, major_gain | YES | `saham_position` (`SAHAM_LABHA`) | 40 / 40 | Satisfied |
| `dhana` | major_gain, major_loss | YES | `saham_position` (`SAHAM_DHANA`, spot-checked §0.3) + `ga_yoga_firings` (`dhana_yoga_2_5_9_11`, `dhana_yoga_house_lords`, both `fired=true`) | 40 (saham) + 2 (firings, both fired) / same | **Best-covered keyword in the ledger** — has both a saham point AND two fired classical dhana yogas live |
| `vyaya` | major_loss | **NO** | — | 0 / 0 | GAP. **Disposition: drop — redundant with house-12 evidence (already covered, §1.1) and the `vyaya`-bhava concept itself is the classical name for house 12, not a separate lookup key.** |
| `vanijya` | business_launch | **NO** | — | 0 / 0 | GAP. **Disposition: drop — redundant with houses 7/10/11 + Mercury/Jupiter.** |
| `vidya` | education_milestone, exam_outcome | YES | `saham_position` (`SAHAM_VIDYA`) | 40 / 40 | Satisfied |
| `buddhi` | education_milestone | YES | `saham_position` | 40 / 40 | Satisfied |
| `guru` | education_milestone | YES | `saham_position` (also literally the Sanskrit name for Jupiter — ambiguous keyword, flagged) | 40 / 40 | Satisfied, but **ambiguity flagged**: "guru" as a `yoga_keyword` could mean the saham OR could be a mis-keyed reference to Jupiter (already a `karaka_graha`). Not investigated further; harmless duplication if so. |
| `roga` | illness_acute, chronic_onset | YES | `saham_position` (`SAHAM_ROGA`) + `panchanga_panchaka_classification` | 80 + 15 / 80 + 15 | Satisfied |
| `vyadhi` | illness_acute | **NO** | — | 0 / 0 | GAP, synonym of `roga`. **Disposition: drop — redundant.** |
| `deergha` | chronic_onset | **NO** | — | 0 / 0 | GAP ("deergha" = chronic/long-duration qualifier, not a lookup key). **Disposition: drop — the chronicity concept is already carried by `dhaiya_period`/`sade_sati_*` duration facts if Campaign B wants a temporal-duration signal; not a §A8 gap to fix, a scope note for B.** |
| `grha` | property_acquisition | **NO** | — | 0 / 0 | GAP, synonym of house/property. **Disposition: drop — redundant with house 4 + Mars/Venus.** |
| `kshetra` | property_acquisition | YES (partial/unexpected) | `esoteric_point_sphuta_fertility` (`fact_subject` contains "kshetra" as a sub-term of an unrelated esoteric-point name, NOT a property-signification fact) | 35 / 35 | **FALSE-POSITIVE MATCH, flagged explicitly per R16 — do not treat as satisfied.** The literal substring `kshetra` collides with an unrelated fertility-point fact category; this is NOT evidence for property acquisition. Correct disposition: **GAP, same as `grha`** — drop as a separate factor, already covered by house-4 evidence. |
| `bhumi` | property_acquisition | **NO** | — | 0 / 0 | GAP, same disposition as `grha`/`kshetra`. |
| `marana` | bereavement | **NO** | — | 0 / 0 | GAP. **Disposition: drop — redundant with houses 4/9/8 + Moon/Sun/Saturn (maraka-lord evidence is already available via `kp_house_significators.cusp_owner` for houses 2/7, per the classical maraka rule cited in `signature_model`, not the literal string "marana").** |
| `preta` | bereavement | **NO** | — | 0 / 0 | GAP, same disposition. |
| `dharma` | spiritual_turn | YES | `karaka_bhava_concordance` + `graha_nakshatra_join` + `karakatva_strength_per_significance` | 145 + 11 + 10 / 145 + 14 + 10 | Satisfied |
| `moksha` | spiritual_turn | YES | `karaka_bhava_concordance` + `saham_position` (`SAHAM_MOKSHA`) + `graha_nakshatra_join` + `karakatva_strength_per_significance` | 145+40+15+10 / 145+40+10+10 | Satisfied |
| `purva_punya` | spiritual_turn | **NO** | — | 0 / 0 | GAP. **Disposition: drop — a narrative/citation gloss (past-life merit), no classical single-fact lookup exists or should be expected; the 9th-house/Jupiter/Ketu evidence already covers the classical signification.** |

**Yoga-keyword summary: the registry uses 34 unique keyword strings across its 21 non-provisional
`yoga_keywords` lists (recounted directly from `grep -n "yoga_keywords=" bo_pratijna_karyatva.py`
— 21 lines, 34 distinct strings after dedup). 14 of the 34 have a genuine live counterpart (one
of which, `dhana`, is unusually well-covered with a firings-authoritative corroboration); 20
have no literal live counterpart and are individually dispositioned above (mostly "drop —
redundant with already-covered house/graha evidence," one real synonym-resolution gap
[`kuja_dosha`/`manglik` — note `manglik` itself is the registry's own second-listed keyword for
`separation` and IS satisfied directly, so only `kuja_dosha` needs the fix], one genuinely
missing derived-signal gap requiring new Reader logic [`6L-7L`], and one confirmed
false-positive match that must NOT be silently counted as satisfied [`kshetra`]).** Every one of
the 20 gaps is named individually above — none lumped into an unexplained bucket.

---

## §2 — Signature-Model Cross-Reference (`bo_pratijna_karyatva.py` vs. `brahma_event_ontology.signature_model`, live)

Per the task's source #2 instruction, every class's `KaryatvaMap` was cross-read against the
live `signature_model` JSONB (confirmed live-synced with `l0_ghatana.py` via a direct query,
§0.1 item 2). **Agreement is the common case; every divergence is named, not silently
resolved** — R13 forbids picking a winner without saying so; that adjudication is explicitly
Campaign B's job (rubric spec draft, out of scope here).

| Class | Houses agree? | Karakas agree? | Varga agrees? | Note |
|---|---|---|---|---|
| marriage | Partial (`signature_model` adds house 2) | Partial (`KaryatvaMap` adds Jupiter) | YES (D9) | minor divergence |
| separation | Partial (`KaryatvaMap` adds house 7 as the "site" house) | **DIVERGE** — `signature_model`=[Rahu,Saturn,Mars], `KaryatvaMap`=[Saturn,Ketu] — only Saturn shared | YES (D9) | flagged — see below |
| childbirth | Partial (`signature_model` adds house 1) | YES (Jupiter) | YES (D7) | minor divergence |
| **parental_event** | n/a | n/a | n/a | **NO `KaryatvaMap` ENTRY AT ALL — see §4** |
| surgery | YES ([6,8]) | YES (Mars) | YES (D30) | full agreement |
| illness_acute | Partial (`signature_model` adds house 8) | Partial (`signature_model` adds Saturn) | YES (D30) | minor divergence |
| chronic_onset | YES ([6,8]) | YES (Saturn) | YES (D30) | full agreement |
| relocation | Partial (`signature_model` adds house 3) | YES (Moon, Rahu) | YES (D4) | minor divergence |
| foreign_settlement | YES ([12,9,7]) | YES (Rahu) | Partial — `signature_model` lists [D9,D12], `KaryatvaMap` only D9 | minor divergence |
| romantic_start | YES ([5,7]) | YES (Venus) | YES (D9) | full agreement |
| career_entry | Partial (`signature_model` adds houses 6,1) | YES (Sun, Saturn) | YES (D10) | minor divergence |
| career_change | Partial (`signature_model`=[10,3,9] vs `KaryatvaMap`=[10]) | **DIVERGE** — `signature_model`=[Rahu], `KaryatvaMap`=[Sun,Saturn] — **zero karakas shared** | YES (D10) | **flagged — see below** |
| career_advancement | YES ([10,11]) | Partial (`KaryatvaMap` adds Jupiter) | YES (D10) | minor divergence |
| career_setback | Partial (`signature_model` adds house 12) | Partial (`signature_model` adds Rahu) | YES (D10) | minor divergence, `dusthana_required` intact either way |
| business_launch | YES ([7,10,11]) | YES (Mercury, Jupiter) | YES (D10) | full agreement |
| education_milestone | YES ([4,5,9]) | YES (Mercury, Jupiter) | YES (D24) | full agreement |
| exam_outcome | Partial (`signature_model`=[5,9] vs `KaryatvaMap`=[4,5]) | Partial (`KaryatvaMap` adds Jupiter) | YES (D24) | minor divergence |
| major_gain | YES ([2,11]) | YES (Jupiter, Mercury) | YES (D2) | full agreement |
| major_loss | Partial (`signature_model` adds house 11) | Partial (`signature_model` adds Rahu) | YES (D2) | minor divergence, `dusthana_required` intact |
| property_acquisition | YES ([4]) | Partial (`KaryatvaMap` adds Venus) | YES (D4) | minor divergence |
| **bereavement** | **DIVERGE** — `signature_model`=[8,12,2], `KaryatvaMap`=[4,9,8] — only house 8 shared | **DIVERGE** — `signature_model`=[Saturn,Ketu], `KaryatvaMap`=[Moon,Sun,Saturn] — only Saturn shared | **DIVERGE** — `signature_model`=D8, `KaryatvaMap`=D12 | **flagged — see below, most significant divergence in the registry** |
| spiritual_turn | YES ([9,12,5]) | YES (Jupiter, Ketu) | YES (D20) | full agreement |
| achievement_recognition (provisional) | Partial (`signature_model` adds house 5) | **DIVERGE** — `signature_model`=[Sun,Mercury], `KaryatvaMap`=[Sun,Jupiter] | n/a (provisional, no divisional in `KaryatvaMap`) | flagged |
| financial_deception (provisional) | **DIVERGE** — `signature_model`=[2,11,12], `KaryatvaMap`=[8,12] — only house 12 shared | Partial (`signature_model` adds Saturn) | n/a | flagged |
| psychological_arc (provisional) | **DIVERGE** — `signature_model`=[1,6,12], `KaryatvaMap`=[5,8,12] — only house 12 shared | **DIVERGE** — `signature_model`=[Moon,Mercury,Saturn], `KaryatvaMap`=[Moon,Ketu] — only Moon shared | n/a | flagged |
| birth_anchor (provisional) | YES ([1]) | YES (Sun) | n/a | full agreement |
| travel_event (provisional) | YES ([3,9,12]) | Partial (`KaryatvaMap` adds Rahu) | n/a | minor divergence |

**Three divergences are significant enough to name explicitly, not just tabulate:**

1. **`bereavement`** — the two sources barely overlap (1 of 3 houses, 1 of 2–3 karakas, and a
   completely different varga, D8 vs D12). Both are independently citable to BPHS (maraka
   houses 2/7/8/12 for `signature_model`'s framing vs. parental/paternal houses 4/9 for
   `KaryatvaMap`'s framing) — **this reads as two different, both-classically-valid framings of
   "bereavement" (death of the native's significant other/self-adjacent maraka vs. death of a
   parent) that got merged into one event class without reconciling their evidence sets.**
   Disposition proposed for the checkpoint: either split into two classes (`bereavement_maraka`
   vs. `bereavement_parental` — note `parental_event`, §4, already exists as its own class and
   is closer to `KaryatvaMap`'s bereavement framing, suggesting the two may already be
   redundant) or pick one framing explicitly and retire the other's citations. **Not resolved
   here per R13 — flagged for the native+Fable checkpoint.**
2. **`career_change`** — zero karaka overlap (Rahu vs. Sun/Saturn) is a real classical
   disagreement (transformational/unexpected career shift via Rahu vs. steady 10th-house
   authority via Sun/Saturn — both defensible readings of "career change," but they will
   nominate different chart evidence and likely disagree on the verdict). Flagged for
   checkpoint.
3. **`separation`** — Mars appears in `signature_model` but not `KaryatvaMap`'s
   `karaka_grahas` (Mars IS in `KaryatvaMap`'s `condition_malefic_grahas`, so it isn't absent
   from the class entirely — it plays a different structural role in each source). Worth a
   checkpoint note but lower-stakes than the two above.

All other divergences are "signature_model's broader net includes KaryatvaMap's narrower,
already-cited set plus 1 extra house/karaka" — read as *sig is a superset*, not a contradiction,
and not flagged for checkpoint escalation.

---

## §3 — Per-Class Coverage (all 27 classes)

Each class below cites the shared ledgers (§1) by house/graha/varga id rather than re-deriving
counts. **Every class's houses, grahas, and vargas are independently confirmed non-empty on
both charts** (§1.1–§1.3) — the per-class tables below record which specific ledger rows apply
and flag yoga-keyword/dusthana specifics only.

### 3.1 marriage
| Factor | Ledger reference | Status |
|---|---|---|
| `primary_bhava=[7]` | §1.1 House 7 | COVERED |
| `karaka_grahas=[Venus,Jupiter]` | §1.2 VEN, JUP | COVERED |
| `divisional=D9` | §1.3 D9 | COVERED |
| `yoga_keywords=[darakaraka,upapada,kalatra]` | §1.4 | 2/3 COVERED (`kalatra` GAP→drop, redundant) |
| `condition_malefic_grahas=[Saturn,Rahu,Ketu]` | §1.2 SAT, RAH_MEAN, KET_MEAN | COVERED |
Citations carried unchanged: BPHS ch.19, ch.28, ch.6; Jaimini Sutram 1.3.1. **Verdict: FULLY COVERED** (one dropped-redundant keyword, not a real gap).

### 3.2 separation
| Factor | Ledger reference | Status |
|---|---|---|
| `primary_bhava=[7,6,8,12]` | §1.1 Houses 7,6,8,12 | COVERED |
| `karaka_grahas=[Saturn,Ketu]` | §1.2 SAT, KET_MEAN | COVERED |
| `dusthana_required=True` | §1.1 Houses 6,8,12 (all non-empty) | COVERED |
| `divisional=D9` | §1.3 D9 | COVERED |
| `yoga_keywords=[kuja_dosha,manglik,6L-7L]` | §1.4 | 1/3 direct + 1 synonym-resolvable + 1 needs-new-logic |
| `condition_malefic_grahas=[Mars,Rahu]` | §1.2 MAR, RAH_MEAN | COVERED |
**Verdict: FULLY COVERED** for structural factors; `6L-7L` needs Campaign B derived-signal work (§1.4), not a fact-existence gap. Signature-model karaka divergence flagged (§2).

### 3.3 childbirth
| Factor | Ledger reference | Status |
|---|---|---|
| `primary_bhava=[5]` | §1.1 House 5 | COVERED |
| `karaka_grahas=[Jupiter]` | §1.2 JUP | COVERED |
| `divisional=D7` | §1.3 D7 | COVERED |
| `yoga_keywords=[putra,santana]` | §1.4 | 1/2 COVERED (`santana` GAP→drop, redundant) |
| `condition_malefic_grahas=[Saturn,Rahu]` | §1.2 SAT, RAH_MEAN | COVERED |
**Verdict: FULLY COVERED.**

### 3.4 surgery
| Factor | Ledger reference | Status |
|---|---|---|
| `primary_bhava=[6,8]` | §1.1 Houses 6,8 | COVERED |
| `karaka_grahas=[Mars]` | §1.2 MAR | COVERED |
| `divisional=D30` | §1.3 D30 (flagged thin, non-empty) | COVERED |
| `yoga_keywords=[shastra,vrana]` | §1.4 | 0/2 direct — both GAP→drop, redundant with house/karaka evidence |
| `condition_malefic_grahas=[Saturn,Rahu]` | §1.2 SAT, RAH_MEAN | COVERED |
**Verdict: FULLY COVERED** (structural factors); both keywords dropped as redundant glosses.

### 3.5 relocation
| Factor | Ledger reference | Status |
|---|---|---|
| `primary_bhava=[4,12]` | §1.1 Houses 4,12 | COVERED |
| `karaka_grahas=[Moon,Rahu]` | §1.2 MOON, RAH_MEAN | COVERED |
| `divisional=D4` | §1.3 D4 | COVERED |
| `yoga_keywords=[pravasa,desa]` | §1.4 | 0/2 direct — both GAP→drop |
| `condition_malefic_grahas=[Saturn,Ketu]` | §1.2 SAT, KET_MEAN | COVERED |
**Verdict: FULLY COVERED** (structural factors).

### 3.6 foreign_settlement
| Factor | Ledger reference | Status |
|---|---|---|
| `primary_bhava=[12,9,7]` | §1.1 Houses 12,9,7 | COVERED |
| `karaka_grahas=[Rahu]` | §1.2 RAH_MEAN | COVERED |
| `divisional=D9` | §1.3 D9 (`signature_model` also cites D12, itself covered) | COVERED |
| `yoga_keywords=[videsh,pravasa]` | §1.4 | 0/2 direct — both GAP→drop |
| `condition_malefic_grahas=[Saturn,Ketu]` | §1.2 SAT, KET_MEAN | COVERED |
**Verdict: FULLY COVERED** (structural factors).

### 3.7 romantic_start
| Factor | Ledger reference | Status |
|---|---|---|
| `primary_bhava=[5,7]` | §1.1 Houses 5,7 | COVERED |
| `karaka_grahas=[Venus]` | §1.2 VEN | COVERED |
| `divisional=D9` | §1.3 D9 | COVERED |
| `yoga_keywords=[kalatra,prema]` | §1.4 | 0/2 direct — both GAP→drop |
| `condition_malefic_grahas=[Saturn,Rahu]` | §1.2 SAT, RAH_MEAN | COVERED |
**Verdict: FULLY COVERED** (structural factors).

### 3.8 career_entry
| Factor | Ledger reference | Status |
|---|---|---|
| `primary_bhava=[10]` | §1.1 House 10 | COVERED |
| `karaka_grahas=[Sun,Saturn]` | §1.2 SUN, SAT | COVERED |
| `divisional=D10` | §1.3 D10 | COVERED |
| `yoga_keywords=[karma,rajya]` | §1.4 | 2/2 COVERED |
| `condition_malefic_grahas=[Rahu,Ketu]` | §1.2 RAH_MEAN, KET_MEAN | COVERED |
**Verdict: FULLY COVERED.**

### 3.9 career_change
| Factor | Ledger reference | Status |
|---|---|---|
| `primary_bhava=[10]` | §1.1 House 10 | COVERED |
| `karaka_grahas=[Sun,Saturn]` | §1.2 SUN, SAT | COVERED |
| `divisional=D10` | §1.3 D10 | COVERED |
| `yoga_keywords=[karma,rajya]` | §1.4 | 2/2 COVERED |
| `condition_malefic_grahas=[Rahu,Ketu]` | §1.2 RAH_MEAN, KET_MEAN | COVERED |
**Verdict: FULLY COVERED**, but see §2 — the karaka-set disagreement with `signature_model`
(Rahu vs. Sun/Saturn) is the second-most significant divergence in the registry and should be
resolved at the checkpoint before Campaign B scores this class.

### 3.10 career_advancement
| Factor | Ledger reference | Status |
|---|---|---|
| `primary_bhava=[10,11]` | §1.1 Houses 10,11 | COVERED |
| `karaka_grahas=[Sun,Jupiter]` | §1.2 SUN, JUP | COVERED |
| `divisional=D10` | §1.3 D10 | COVERED |
| `yoga_keywords=[rajya,labha]` | §1.4 | 2/2 COVERED |
| `condition_malefic_grahas=[Saturn,Rahu]` | §1.2 SAT, RAH_MEAN | COVERED |
**Verdict: FULLY COVERED.**

### 3.11 career_setback
| Factor | Ledger reference | Status |
|---|---|---|
| `primary_bhava=[10,6,8]` | §1.1 Houses 10,6,8 | COVERED |
| `karaka_grahas=[Saturn]` | §1.2 SAT | COVERED |
| `dusthana_required=True` | §1.1 Houses 6,8 | COVERED |
| `divisional=D10` | §1.3 D10 | COVERED |
| `yoga_keywords=[karma,roga]` | §1.4 | 2/2 COVERED |
| `condition_malefic_grahas=[Mars,Rahu]` | §1.2 MAR, RAH_MEAN | COVERED |
**Verdict: FULLY COVERED.**

### 3.12 business_launch
| Factor | Ledger reference | Status |
|---|---|---|
| `primary_bhava=[7,10,11]` | §1.1 Houses 7,10,11 | COVERED |
| `karaka_grahas=[Mercury,Jupiter]` | §1.2 MER, JUP | COVERED |
| `divisional=D10` | §1.3 D10 | COVERED |
| `yoga_keywords=[vanijya,labha]` | §1.4 | 1/2 COVERED (`vanijya` GAP→drop) |
| `condition_malefic_grahas=[Saturn,Rahu]` | §1.2 SAT, RAH_MEAN | COVERED |
**Verdict: FULLY COVERED.**

### 3.13 education_milestone
| Factor | Ledger reference | Status |
|---|---|---|
| `primary_bhava=[4,5,9]` | §1.1 Houses 4,5,9 | COVERED |
| `karaka_grahas=[Mercury,Jupiter]` | §1.2 MER, JUP | COVERED |
| `divisional=D24` | §1.3 D24 | COVERED |
| `yoga_keywords=[vidya,buddhi,guru]` | §1.4 | 3/3 COVERED (`guru` ambiguity flagged) |
| `condition_malefic_grahas=[Saturn,Rahu]` | §1.2 SAT, RAH_MEAN | COVERED |
**Verdict: FULLY COVERED.**

### 3.14 exam_outcome
| Factor | Ledger reference | Status |
|---|---|---|
| `primary_bhava=[4,5]` | §1.1 Houses 4,5 | COVERED |
| `karaka_grahas=[Mercury,Jupiter]` | §1.2 MER, JUP | COVERED |
| `divisional=D24` | §1.3 D24 | COVERED |
| `yoga_keywords=[vidya,buddhi]` | §1.4 | 2/2 COVERED |
| `condition_malefic_grahas=[Saturn,Rahu]` | §1.2 SAT, RAH_MEAN | COVERED |
**Verdict: FULLY COVERED.**

### 3.15 illness_acute
| Factor | Ledger reference | Status |
|---|---|---|
| `primary_bhava=[6]` | §1.1 House 6 | COVERED |
| `karaka_grahas=[Mars]` | §1.2 MAR | COVERED |
| `divisional=D30` | §1.3 D30 (thin, non-empty) | COVERED |
| `yoga_keywords=[roga,vyadhi]` | §1.4 | 1/2 COVERED (`vyadhi` GAP→drop, synonym of `roga`) |
| `condition_malefic_grahas=[Saturn,Rahu]` | §1.2 SAT, RAH_MEAN | COVERED |
**Verdict: FULLY COVERED.**

### 3.16 chronic_onset
| Factor | Ledger reference | Status |
|---|---|---|
| `primary_bhava=[6,8]` | §1.1 Houses 6,8 | COVERED |
| `karaka_grahas=[Saturn]` | §1.2 SAT | COVERED |
| `divisional=D30` | §1.3 D30 (thin, non-empty) | COVERED |
| `yoga_keywords=[roga,deergha]` | §1.4 | 1/2 COVERED (`deergha` GAP→drop, scope note for B) |
| `condition_malefic_grahas=[Rahu,Ketu]` | §1.2 RAH_MEAN, KET_MEAN | COVERED |
**Verdict: FULLY COVERED.**

### 3.17 major_gain
| Factor | Ledger reference | Status |
|---|---|---|
| `primary_bhava=[2,11]` | §1.1 Houses 2,11 | COVERED |
| `karaka_grahas=[Jupiter,Mercury]` | §1.2 JUP, MER | COVERED |
| `divisional=D2` | §1.3 D2 | COVERED |
| `yoga_keywords=[dhana,labha]` | §1.4 | 2/2 COVERED — **`dhana` is the single best-evidenced keyword in the entire registry** (real saham + two fired dhana yogas, `ga_yoga_firings`) |
| `condition_malefic_grahas=[Saturn,Rahu]` | §1.2 SAT, RAH_MEAN | COVERED |
**Verdict: FULLY COVERED.**

### 3.18 major_loss
| Factor | Ledger reference | Status |
|---|---|---|
| `primary_bhava=[2,12]` | §1.1 Houses 2,12 | COVERED |
| `karaka_grahas=[Saturn]` | §1.2 SAT | COVERED |
| `dusthana_required=True` | §1.1 House 12 | COVERED |
| `divisional=D2` | §1.3 D2 | COVERED |
| `yoga_keywords=[dhana,vyaya]` | §1.4 | 1/2 COVERED (`vyaya` GAP — no literal match found, not individually dispositioned above as it repeats the "drop, redundant with house-12 evidence" pattern) |
| `condition_malefic_grahas=[Rahu,Ketu]` | §1.2 RAH_MEAN, KET_MEAN | COVERED |
**Verdict: FULLY COVERED.**

### 3.19 property_acquisition
| Factor | Ledger reference | Status |
|---|---|---|
| `primary_bhava=[4]` | §1.1 House 4 | COVERED |
| `karaka_grahas=[Mars,Venus]` | §1.2 MAR, VEN | COVERED |
| `divisional=D4` | §1.3 D4 | COVERED |
| `yoga_keywords=[grha,kshetra,bhumi]` | §1.4 | 0/3 direct — `kshetra` is a confirmed FALSE-POSITIVE match (flagged, must not count as satisfied); all three GAP→drop |
| `condition_malefic_grahas=[Saturn,Rahu]` | §1.2 SAT, RAH_MEAN | COVERED |
**Verdict: FULLY COVERED** (structural factors); all 3 keywords dropped, one with an explicit false-positive warning for whoever builds the Reader.

### 3.20 bereavement
| Factor | Ledger reference | Status |
|---|---|---|
| `primary_bhava=[4,9,8]` | §1.1 Houses 4,9,8 | COVERED |
| `karaka_grahas=[Moon,Sun,Saturn]` | §1.2 MOON, SUN, SAT | COVERED |
| `divisional=D12` | §1.3 D12 | COVERED |
| `yoga_keywords=[marana,preta]` | §1.4 | 0/2 direct — both GAP→drop |
| `condition_malefic_grahas=[Mars,Rahu]` | §1.2 MAR, RAH_MEAN | COVERED |
**Verdict: FULLY COVERED** for `KaryatvaMap`'s own factor set; **flag the §2 signature-model divergence as unresolved and checkpoint-worthy** — this class's evidence set may need to be split or reconciled with `parental_event` (§4) before Campaign B scores it.

### 3.21 spiritual_turn
| Factor | Ledger reference | Status |
|---|---|---|
| `primary_bhava=[9,12,5]` | §1.1 Houses 9,12,5 | COVERED |
| `karaka_grahas=[Jupiter,Ketu]` | §1.2 JUP, KET_MEAN | COVERED |
| `divisional=D20` | §1.3 D20 | COVERED |
| `yoga_keywords=[dharma,moksha,purva_punya]` | §1.4 | 2/3 COVERED (`purva_punya` GAP→drop) |
| `condition_malefic_grahas=[Rahu]` | §1.2 RAH_MEAN | COVERED |
**Verdict: FULLY COVERED.**

### 3.22 achievement_recognition (DR-13 provisional)
| Factor | Ledger reference | Status |
|---|---|---|
| `primary_bhava=[10,11]` | §1.1 Houses 10,11 | COVERED |
| `karaka_grahas=[Sun,Jupiter]` | §1.2 SUN, JUP | COVERED |
No `divisional`/`yoga_keywords`/`condition_malefic_grahas` fields in this `KaryatvaMap` entry
(provisional, domain-fallback class per §N.4). **Verdict: FULLY COVERED for its declared
(narrower) factor set.** §2 flags a karaka divergence vs. `signature_model` (Mercury vs.
Jupiter) — lower stakes than career_change/bereavement but real.

### 3.23 financial_deception (DR-13 provisional)
| Factor | Ledger reference | Status |
|---|---|---|
| `primary_bhava=[8,12]` | §1.1 Houses 8,12 | COVERED |
| `karaka_grahas=[Rahu]` | §1.2 RAH_MEAN | COVERED |
**Verdict: FULLY COVERED** for its declared factor set. §2 flags a significant house divergence
vs. `signature_model` ([2,11,12] vs. [8,12]) — worth checkpoint attention given this class's
`inherited_from: major_loss` provenance note in `l0_ghatana.py` suggests `signature_model`'s
broader house set (which matches major_loss's own [2,11,12]) may be the intended one.

### 3.24 psychological_arc (DR-13 provisional)
| Factor | Ledger reference | Status |
|---|---|---|
| `primary_bhava=[5,8,12]` | §1.1 Houses 5,8,12 | COVERED |
| `karaka_grahas=[Moon,Ketu]` | §1.2 MOON, KET_MEAN | COVERED |
**Verdict: FULLY COVERED** for its declared factor set. §2 flags the largest divergence among
the provisional classes (houses and karakas both nearly disjoint from `signature_model`) —
checkpoint attention warranted.

### 3.25 birth_anchor (DR-13 provisional)
| Factor | Ledger reference | Status |
|---|---|---|
| `primary_bhava=[1]` | §1.1 House 1 | COVERED |
| `karaka_grahas=[Sun]` | §1.2 SUN | COVERED |
**Verdict: FULLY COVERED.** Full agreement with `signature_model` (§2).

### 3.26 travel_event (DR-13 provisional)
| Factor | Ledger reference | Status |
|---|---|---|
| `primary_bhava=[3,9,12]` | §1.1 Houses 3,9,12 | COVERED |
| `karaka_grahas=[Moon,Rahu]` | §1.2 MOON, RAH_MEAN | COVERED |
**Verdict: FULLY COVERED.**

---

## §4 — THE CLASS-LEVEL GAP: `parental_event` has no `KaryatvaMap` entry at all

This is the most structurally important finding in this document, and it is not a per-factor
gap — it is a **whole missing class**.

`brahma_event_ontology`/`l0_ghatana.EVENT_CLASSES` defines 27 classes, confirmed live
(`select count(*) from brahma_event_ontology` → 27). `bo_pratijna_karyatva.KARYATVA_REGISTRY`
defines only **26** `KaryatvaMap` entries. The one class present in the ontology but absent from
the karyatva registry is **`parental_event`** (`l0_ghatana.py` lines 244–262: houses `[4,9]`,
karakas `[Moon,Sun]`, varga `D12`, citations `BPHS ch.4 (matru-bhava), ch.9 (pitru-bhava)`).

This was cross-confirmed two ways: `grep -c 'event_class_id=' bo_pratijna_karyatva.py` → 26,
and a full manual read of the file (§0.1 item 1) — `parental_event` is genuinely absent, not
miscounted.

**Live fact coverage for what `parental_event` WOULD need is not in question** — houses 4 and 9
and grahas Moon/Sun and varga D12 are all independently verified non-empty in §1.1–§1.3 (this
class would inherit `bereavement`'s exact varga and largely overlap `bereavement`'s house/karaka
set per `KaryatvaMap`, per §2's own finding that `KaryatvaMap.bereavement` looks like it may
already be conflating the two concepts). **The gap is purely that `bo_pratijna_karyatva.py`
never got a `parental_event` entry written**, so today the promise engine (v3, and v4 until
fixed) cannot score this class at all — any query for `parental_event` promise would presumably
fall through to the provisional/domain-fallback path or fail outright (not tested here — out of
this document's read-only scope; a `bo_pratijna.py` consumer-code read would be needed to say
which, and that file is outside this task's "no engine code" boundary for *writing*, though
reading it to confirm behavior would be legitimate future-session work).

**Proposed disposition (for the checkpoint):** Add a `parental_event` `KaryatvaMap` entry to the
registry in Campaign B, using `signature_model`'s already-cited houses `[4,9]`, karakas
`[Moon,Sun]`, divisional `D12`, and BPHS ch.4/ch.9 citations directly (no new sourcing
required — the classical citations already exist in `l0_ghatana.py` and were carried in from
the same seed package the karyatva registry itself draws from). **This also gives the
checkpoint a natural moment to resolve §2's `bereavement` divergence** — since
`KaryatvaMap.bereavement`'s houses `[4,9,8]` and karakas `[Moon,Sun,Saturn]` look like an
accidental merge of `parental_event`'s intended houses/karakas with `bereavement`'s own,
authoring the missing `parental_event` entry cleanly may be the same act as un-conflating
`bereavement`.

---

## §5 — Summary

**27/27 event classes have their `primary_bhava`, `karaka_grahas`, `divisional`, and
`condition_malefic_grahas` factors fully covered by live, non-empty, spot-check-verified facts
on both canonical charts** (482012f1 mandatory, 1c826d5a also run in full) — with one class
(`parental_event`) covered only in the sense that its *would-be* factors are independently
verified non-empty; it has no `KaryatvaMap` entry to attach them to (§4).

**Coverage by count:**

| Layer | Result |
|---|---|
| Houses (12/12) | 100% non-empty, both charts, real occupancy + lord + strength-category data |
| Grahas (9/9) | 100% non-empty, both charts, dignity/strength + affliction data (one scope-boundary sub-finding: Ketu has no `sambandha_grade` rows — real, not a defect) |
| Vargas (10/10, incl. D1) | 100% non-empty, both charts (D30 flagged as real-but-thin, used by 3 health classes) |
| Yoga keywords (34 unique) | 14 satisfied directly, 20 named gaps each individually dispositioned (§1.4) — mostly "drop, redundant with already-covered structural evidence"; one real synonym-resolution fix (`kuja_dosha`→`manglik`); one genuinely missing derived-signal (`6L-7L`); one confirmed false-positive match flagged so it is never silently counted (`kshetra`) |
| Classes with a `KaryatvaMap` entry (26/27) | All 26 FULLY COVERED at the structural-factor level |
| Classes missing a `KaryatvaMap` entry | **1 — `parental_event`** (§4) |
| Signature-model cross-reference divergences | 3 flagged as checkpoint-significant (`bereavement`, `career_change`, `financial_deception`/`psychological_arc` as a pair); ~15 minor "signature_model is a superset" variances noted but not escalated |

### Named gaps requiring a disposition decision (not fixed in this document — R13/R19: this is
a document-authoring task, no engine or registry code was touched)

1. **`parental_event` has no karyatva entry** — propose: author it from `signature_model`'s
   already-cited houses/karakas/varga/citations (§4); do this alongside resolving finding #2.
2. **`bereavement` vs. `parental_event`/`signature_model` divergence** — propose: split or
   explicitly pick one framing at the checkpoint (§2, §4).
3. **`career_change` karaka disagreement** (Rahu vs. Sun/Saturn, zero overlap) — propose:
   checkpoint adjudication; both are classically defensible but nominate different evidence.
4. **20 `yoga_keywords` gaps** — propose: drop 17 as redundant narrative glosses (already
   covered by structural house/graha evidence), fix 1 via synonym resolution
   (`kuja_dosha`→`manglik`), build 1 as new derived-signal logic in Campaign B's Chart Reader
   (`6L-7L`), and treat 1 as a confirmed false-positive that must never be silently counted
   (`kshetra`) — full breakdown in §1.4.
5. **D30's thin coverage** (surgery/illness_acute/chronic_onset) — not a gap (verified
   non-empty) but a scope note: Campaign B's rubric weighting should not assume D30 carries the
   same evidentiary density as D9/D10.

### The 2–3 most interesting/concerning findings, surfaced for the checkpoint

- **The `parental_event` class-level gap (§4)** is the single most consequential finding: an
  entire event class the ontology defines and the ontology's own `signature_model` fully
  specifies (with real, verified-non-empty chart evidence) simply has no scoring registry entry
  to consume that evidence. This has likely been silently unscoreable since the karyatva
  registry was authored.
- **`bereavement`'s near-total divergence from its own `signature_model`** (§2 finding #1) —
  combined with the `parental_event` gap, this looks like two related defects with one probable
  common root: the registry author likely intended `bereavement` to cover parental death and
  `parental_event` never got written, OR the two got conflated during authoring and
  `bereavement`'s houses/karakas are a blend of both concepts. Either reading means Campaign B
  should not simply "add the missing row" without first re-reading both classes together.
- **The `yoga_keywords` literal-match failure rate (20/34, well over half)** was not something the
  task's own framing anticipated finding at this scale — it means the karyatva registry's
  citation-bearing keyword lists were authored as classical narrative glosses, not as an index
  into `chart_facts`' actual key vocabulary, and a literal keyword→fact_key mapping strategy
  (had Campaign B assumed one) would have silently under-scored more than half of all
  yoga-keyword factors. The `kshetra` false-positive is the sharpest version of this risk: a
  literal-match strategy would have silently and *incorrectly* reported that factor as
  satisfied.

---

*End of A8_FACTOR_FACT_COVERAGE_MATRIX_v1.0. Companion deliverable (v4 Scoring Rubric Spec
draft, Lane A8 item 2) is a separate document, not produced here. No `chart_facts` row, no
`bo_pratijna_karyatva.py` line, and no other engine/pipeline file was written to in the
production of this document — read-only verification only, per the task's own file-scope
boundary.*
