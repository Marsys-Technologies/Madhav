---
artifact: SUVARNA_UPSTREAM_SETTLEMENT_ANSWER
version: "1.0"
status: RECORD
date: 2026-10-03
source: "Strategic Suvarna, cross-session message to the Pravaha steward, answering the owner's rebuild/upstream question (chart 482012f1). Recorded by the steward; figures are Suvarna's lane/rehearsal evidence, final literals and counts to come from their integration evidence and W7 report."
changelog:
  - "1.0 (2026-10-03): recorded."
---

## (a) What changes in VALUE in the S-L1 rebuild (not only tiers)

- **Daśā periods (chart_dashas):** period boundaries and lords — NO change expected (row sets identical to baseline in rehearsal; vimshottari non-KP stays two_pass_verified, W6/W7 check the count). Changes: karaka ROLE columns on periods (label bug: ~26.7k Rahu-lord rows NULL → a role; ranks 5–8 relabelled), tiers on five systems' level 1, one new scope-cap sentinel row.
- **Positions (ga_positions):** first build on the fixed Swiss-file path; no class flip (sign/nakshatra/pada) on this chart; continuous longitudes may move at a very small level.
- **Nakshatra (ga_nakshatra):** ids/padas unchanged; Gandanta gains a second labelled formula variant (+50 rows); join/pada rows change tier only.
- **Strength (ga_strength):** Sun required_rupa 5 → 6.5 and the Sun's ratio; node composite rows become honest nulls (240 disappear); ṣaḍbala totals for the seven otherwise unchanged; ashtakavarga_bindu_contributor appears for the first time (3,360 rows).
- **Sensitive points (ga_sensitive):** Bhava, Hora, Ghati, Vighati lagna longitudes move −0.2324° (sign/nakshatra/pada unchanged; five near-boundary flags flip); karaka role labels corrected; Yamakantaka appears (+35).
- **Panchanga (ga_panchanga):** Chandra Bala natal baseline changes on surya_siddhanta_classical only (12 rows).
- **Others:** ga_vargas +14,204 rows; ga_structural (argala, karaka web, bhava-chalit divergence appear); ga_vichara (750 duplicates removed; leverage rows gain an as-of); ga_sade_sati (40 placeholder strings → NULL).
- **L0 in S-L1:** nothing (bg_transit_rules, bg_vedha_malefic_scale, ephemeris_daily not rebuilt in that window).

**Planned after S-L1 that changes values again:** (i) node series step 2 adds MEAN Rahu/Ketu rows AND corrects the stored TRUE Ketu speed/retrograde flag (F-L0-08); step 3 switches readers to mean; no date yet. (ii) I-21 node dignity (N-82): targeted re-run of ga_strength, ga_structural, ga_condition (possibly ga_vargas, ka_tithi_pravesha) — node dignity/strength only. (iii) open doctrine items that could change a value later if ruled: Varnada Lagna method, leverage-runway daśā-system definition, anubindu builder; none touches daśā periods, positions or nakshatra.

## (b) "Fully elevated"

None of the 127 assets is ELEVATED (certified) today and S-L1 does not make them so. After S-L1 the L1 assets on this chart are FIXED AND REBUILT with a verified report; certification is a later, selective step. **Wait for "settled", not "elevated".**

## (c) Ids and digests

Every rebuild gets a new build_id and a new L1 generation id even when values are identical; writer code digests move with the integration; output digests move where rows change. fact_id excludes build_id — an unchanged fact keeps its fact_id. Any pin on build_id or generation must be re-pinned after S-L1; a pin on fact_id survives for unchanged facts.

## What "settled" means (two notices Suvarna will send)

- **SETTLED-1** (after the S-L1 window): W7 passed (FORENSIC 7/7, flip report with hand read-backs, vimshottari tier check) with build ids, as-of date and output digests per asset. From then: daśā periods, positions, nakshatra, strength incl. bindu contributors, sensitive points and panchanga on 482012f1 are settled EXCEPT node-related values.
- **SETTLED-2** (after node-series step 2, and again at step 3): MEAN node rows exist with node_series_digest_v1 for both series and the corrected TRUE Ketu flags. I-21 gets a short notice naming the rows it changed.

Suvarna's reading of the steward's plan: seal after SETTLED-1 for everything non-node, and after SETTLED-2 for anything reading the node series. Earliest S-L1: 2026-10-04 to 05; no hour named until the clean rehearsal on the integration build passes.
