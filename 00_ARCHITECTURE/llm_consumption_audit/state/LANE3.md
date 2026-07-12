---
lane: "3"
title: "Cross-serving-path consistency — inconsistent quantities (both values)"
status: CURRENT
generated: 2026-07-12
source: llm_consumption_audit / WIRE state (shard 3-b0)
chart: 482012f1-710e-4a25-994a-93821f5871aa
grahas_probed: Sun, Saturn
ayanamshas: krishnamurti, lahiri_chitrapaksha, raman, surya_siddhanta_classical, true_chitra (5)
---

# LANE 3 — Cross-Serving-Path Consistency

Method: for each quantity served by >1 path, retrieve via each path (DB truth + surgical wire) per (graha × ayanamsha) and DIFF. Per §N.5, `chart_facts` is authoritative over L2+/denormalized copies.

## Paths under test

- **chart_facts** — DB `chart_facts`; wire `query_chart_facts` (`ok:true`, defaults `ayanamsha=lahiri_chitrapaksha`, pivoted; NOTE `fact_subject`/`fact_category` filters appear IGNORED — full dump returned).
- **chart_dashas** — DB `chart_dashas` (denormalized natal-lord metadata); wire `query_dasha_periods` (`ok:true`, serves `lord_natal_*` incl. dignity+shadbala, inherits DB verbatim incl. NULLs).
- **get_signals** — wire returns `Tool not in surgical whitelist: get_signals` → full-pipeline-only, UNREACHABLE (LCA-2). `query_signals`→`msr_sql` used as surgical substitute where noted.

## CONSISTENT quantities (no finding)

| Quantity | Paths | Result |
|---|---|---|
| sign | chart_dashas, chart_facts | Sun=Capricorn, Saturn=Libra — MATCH all 5 ay |
| house | chart_dashas, chart_facts | Sun=10, Saturn=7 — MATCH all 5 ay |
| nakshatra | chart_dashas, chart_facts | MATCH ayanamsha-by-ayanamsha (Sun Dhanishta/Shravana flip is legitimate boundary variation at 293°20′; both paths agree per-ay) |
| pada | chart_facts only | single-path, no cross-check possible |

## INCONSISTENT quantities (findings — both values recorded)

### D3-DIGNITY — chart_dashas drops dignity to NULL on the DEFAULT ayanamsha (class 3 + class 2, HIGH)

Authoritative side = `chart_facts`. `chart_dashas` is the wrong side.

| Path | Saturn (Libra) | Sun (Capricorn) |
|---|---|---|
| **chart_facts (AUTH)** | `is_exalted=true` all 5 ay; `effective_dignity_score=0.975`; `graha_dignity_per_varga.D1_SAT.dignity_state=exalted` | `is_exalted=false` all 5 ay; `effective_dignity_score=0.5`; `D1_SUN.dignity_state=neutral` |
| **chart_dashas** `lord_natal_dignity_d1` | `exalted` for krishnamurti/raman/surya; **NULL** for lahiri_chitrapaksha + true_chitra | `enemy_sign` for krishnamurti/raman/surya; **NULL** for lahiri_chitrapaksha + true_chitra |

DIFF: `chart_facts` says Saturn exalted / Sun non-exalted for ALL 5 ayanamshas; `chart_dashas` drops dignity to **NULL for exactly 2 of 5 ayanamshas — lahiri_chitrapaksha (the DEFAULT) and true_chitra** — even though `lord_natal_sign` is stably Libra/Capricorn (dignity is a pure function of sign, so it cannot legitimately be NULL when sign is present). WRONG value over the wire (NULL ≠ exalted) AND cross-path INCONSISTENT on the default ayanamsha. The `query_chart_facts` wire default (`lahiri_chitrapaksha`) is exactly the ayanamsha where the dasha path returns NULL — the serving-default mismatch amplifies the divergence. Signals substitute (`query_signals`→`msr_sql`) surfaces Saturn D1 `dignity_state=exalted`, CONSISTENT with the authoritative side. Suspected layer: `ka_*` dasha-lord metadata denormalization JOIN drops dignity for lahiri + true_chitra.

### D3-SHADBALA — chart_dashas facet is an EMPTY SHELL, always NULL (class 4 + class 3, MEDIUM-HIGH)

Authoritative side = `chart_facts`; `chart_dashas` facet entirely empty.

| Path | Saturn shadbala (rupa) | Sun shadbala (rupa) |
|---|---|---|
| **chart_facts (AUTH)** `graha_shadbala_total.rupa` | 7.83 (krishnamurti/lahiri/surya/true_chitra), 7.57 (raman) | 8.47 (krishnamurti/lahiri/surya/true_chitra), 8.92 (raman) |
| **chart_dashas** `lord_natal_shadbala_total` | **NULL** all rows, all 5 ay, all levels | **NULL** all rows, all 5 ay, all levels |

DIFF: `chart_facts` holds real shadbala rupa (7.57–8.92); `chart_dashas.lord_natal_shadbala_total` is uniformly NULL — the column is advertised in schema and serialized over the wire (`"lord_natal_shadbala_total":null`) but never populated. A consumer reading shadbala from the dasha path gets nothing; the value exists only via `chart_facts`, forcing an undisclosed second-tool lookup (class-9 candidate). `get_signals` third path UNREACHABLE (LCA-2); no shadbala signal appears on Saturn's top-50 signal surface, so shadbala is effectively single-path = `chart_facts`. Suspected layer: dasha-lord shadbala denormalization never wired to `chart_facts.graha_shadbala_total`.

## Class-9 note (ungoverned judgment, LOW)

Dignity vocabulary mismatch across paths: `chart_facts` expresses dignity only as `is_exalted` (bool) + `effective_dignity_score` (numeric 0–1) + `graha_dignity_per_varga.dignity_state` (categorical), while `chart_dashas` uses categorical `exalted`/`enemy_sign`/`neutral_sign`. A consumer cross-checking must self-translate (score 0.5 ⇄ `enemy_sign`? `neutral`?) — an undocumented mapping the system does not govern.

## Coverage honesty

- Cross-checkable & CONSISTENT: sign, house, nakshatra.
- Cross-checkable & INCONSISTENT: **dignity, shadbala** (both values recorded above).
- Single-path (no cross-check): pada (chart_facts only), dasha_lord_metadata bundle (chart_dashas only).
- Third path `get_signals` for dignity+shadbala: UNREACHABLE (LCA-2), not independently re-audited.
</content>
