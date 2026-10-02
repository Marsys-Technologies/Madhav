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

## Addendum (2026-10-03, Suvarna, verified by reader + code read) — the ten position rows and the gate

- All ten rows exist today on 482012f1: graha_position / longitude_sidereal / lahiri_chitrapaksha; subjects LAGNA, SUN, MOON, MAR, MER, JUP, VEN, SAT, RAH_MEAN, KET_MEAN; exactly one row each; tier `single` on all ten; one build, 1c092ffb-72eb-4614-8422-552ca6eae985.
- ga_positions computes the MEAN node itself (swe.MEAN_NODE pinned for all ayanamshas) and reads nothing from ephemeris_daily: node-series steps 2 and 3 cannot change these rows. Only ga_positions writes graha_position; I-21 and the special-lagna fix do not touch positions.
- The rows are rewritten ONCE, at S-L1, by the unchanged code path: values expected identical, tier stays `single`, build_id new.
- CORRECTION on ids: the chart_facts fact_id formula may INCLUDE build_id since #2607 — assume the ten fact_ids CHANGE at S-L1 until Suvarna confirms per writer. A re-pin after S-L1 is needed regardless.
- SETTLED-1 will carry: for the ten rows fact_id, value at full stored precision, tier, build_id; for vimshottari lahiri levels 1–3 the build id and row count. Pravaha computes the 1206 digest after the protected window and sends it back.
- Agreed gate: **first Gochara seal = SETTLED-1 + the Pravaha daśā re-pin.**

## Addendum 2 (2026-10-03, Suvarna, settled by a production read + writer code) — fact_id stability

For the ten graha_position rows: fact_id = sha256(category|subject|key|chart_id|ayanamsha_id)[:16] with NO build_id (430 of 430 graha_position rows on 482012f1 match). Their fact_ids are STABLE across S-L1; the earlier caution is withdrawn for these rows. At S-L1 each row's build_id changes (inside the Pravaha digest preimage → the digest moves; re-pin still needed) and computed_at (excluded); values expected identical; tier stays `single`. Every OTHER chart_facts category on this chart (outside graha_position / bhava_cusps / house_chalit) has ids built with the old formula including build_id: they change once at S-L1 and are stable afterwards.
