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

## Addendum 3 (2026-10-03, Suvarna) — resonance map references go stale once at S-L1

gochara_resonance_map.target_ref on 482012f1 holds 88 rows citing 17 chart_facts fact_ids outside graha_position / bhava_cusps / house_chalit; those ids change once at S-L1. Rewriting target_ref would change contact/window ids and class_fingerprint, and nothing resolves those refs by id at serve time. DECISION (steward, agreed with Suvarna): no hand re-link; the resonance re-run after SETTLED-1 cites the new ids. Suvarna captures an old-id → natural-key map for the whole chart before the window (with sha256); path to be recorded here. KNOWN LIMIT: between S-L1 and the resonance re-run the 88 rows cite ids that no longer resolve.

## Addendum 4 (2026-10-03, Suvarna) — stored rows verified; CORRECTION: values DO move at S-L1 (Moshier → Swiss .se1)

1. **Stored 2026-09-08 rows are not off by the ayanamsha gap.** Independent check on linux/amd64: all 45 planetary longitudes (5 ayanamshas × 9 grahas) match an independent raw Swiss derivation to < 0.001″; lagna matches (0.00″ on Lahiri); 200/200 D1/D9 varga rows match; the Vimshottari Saturn mahadasha start matches within ±0.5 s on all five ayanamshas. No exposed per-thread site on the S-L1 path (~30 safe, 8 order-dependent, being fixed).
2. **CORRECTION.** The stored rows were built on the MOSHIER fallback, not the Swiss .se1 files. S-L1 is the first build on .se1 (#2860). At S-L1: graha_position longitudes move by under 1″ (Moon +0.665″, Mars +0.118″, Jupiter +0.202″, se1 minus Moshier) and **Vimshottari boundaries move by about 1.94 hours** (Moon-anchored; likewise other Moon-anchored systems). Lords and row counts should hold; boundaries will not. Class values (sign, nakshatra, pada): no flip in the earlier compare; being re-checked on the integration build on Linux. The earlier statement "period boundaries: no change expected" is withdrawn.
3. Consequence for Pravaha: the ten-row longitude digest and the vimshottari digest both move at S-L1 for a real VALUE reason, not only build_id. SETTLED-1 will carry the new values at full precision and the measured boundary shift per level. After S-L1 the L1 rows are se1-based.
4. gochara_v3 fragile sites independently confirmed (engine.py:768; mechanisms/w30_nodal_drishti.py:227 — failing case: empty resonance_targets, or every primitive raising before the first position call on a pool thread). Evidence (read-only, hashed): /Users/Dev/suvarna-evidence/SwissThreadMode/.

## Addendum 5 (2026-10-03, Suvarna) — replace-not-accrete, and the partial-window caveat

By the L1 standard (per-chart delete-then-insert scoped to the natural key) a COMPLETED S-L1 leaves only the new build's vimshottari rows in chart_dashas (build 1f89fd4c gone) and exactly one graha_position row per subject and ayanamsha; the Pravaha writer then refuses until re-pinned. CAVEAT: ga_dashas is a heavy writer (~41 partitions, each substep commits); DURING its run, and after a run that FAILS part-way, chart_dashas holds a mix of old-build and new-build partitions. Vimshottari lahiri is one partition (old or new, never both), but "the pinned build's rows are present" remains true until that partition is rebuilt, and a failed window could leave it old while other L1 assets are new. Suvarna will not send SETTLED-1 unless every one of the 18 assets completed. Exact delete scope being confirmed from the writers.

**STEWARD RULE (binding, ST-SL1-HOLD):** from the start of Suvarna's S-L1 window until SETTLED-1 is received AND the daśā re-pin is merged, NO Gochara build, verification, brief or measurement extract runs on chart 482012f1 — dry runs included. The gate is the SETTLED-1 notice, not "the pinned rows are present".

## Addendum 6 (2026-10-03, Suvarna, confirmed from writer code on the integration branch + live counts) — delete scope and the mechanical guard

After a COMPLETED S-L1, build 1f89fd4c and the new build cannot coexist in chart_dashas for any (system, ayanamsha, level, period): the delete is by chart + system list + ayanamsha list with no build_id/level/date filter; all 45 system×ayanamsha partitions and the scope-cap partition are deleted across all builds and re-inserted (vimshottari and vimshottari_kp share one delete and one insert). graha_position: delete by chart + category + ayanamsha. Primary keys (fact_id, dasha_row_id) are built without build_id, so a surviving old row would make the insert fail loudly. DURING a run and after a PART-FAILED run: mixed state (each ga_dashas partition is its own savepoint and commit). MECHANICAL GUARD recommended beside "SETTLED-1 received": for the chart, exactly ONE distinct build_id across chart_dashas, the complete shape (45 non-scope partitions + 1 scope-cap), AND asset_throughput.state = 'lit' for ga_dashas. Today's baseline on 482012f1: one build per asset (ga_dashas 1f89fd4c, ga_vargas 0663e31b), zero multi-build partitions, zero natural-key duplicates. Suvarna's W7 asserts the same after the window; SETTLED-1 is not sent otherwise.

## Addendum 7 (2026-10-03, Suvarna, MEASURED on linux/amd64 with pinned .se1 and the real daśā builders; harness first reproduced the stored rows exactly) — replaces "~2 h, counts unchanged" beyond Vimshottari levels 1–3

- **Shift (se1 − stored Moshier), near-constant per system:** Vimshottari +6,990 to +6,994 s by ayanamsha (≈1 h 56 m); Kalachakra +145,089 to +145,111 s (≈40 h 18 m; Surya Siddhanta +150,309 s); Yogini, Ashtottari, Chara, Narayana, Naisargika exactly 0 s; Mudda 0 to +1 s except one −43 s bisection step on true_chitra's 2001 varsha.
- **Row counts:** levels 1–3 of every system keep row sets and lords. LEVEL 4 changes for Vimshottari and Kalachakra (the writer drops a period whose UTC start date is not before its end date; the shift moves some short Sukshma periods across midnight): Vimshottari L4 lahiri / true_chitra / krishnamurti / raman / surya_siddhanta 8,165→8,177, 8,164→8,166, 8,155→8,156, 8,043→8,034, 7,983→7,977 (five-ayanamsha total stays 40,510 by coincidence — do not check the total); Kalachakra L4 +3 / 0 / +10 / −8 / −20.
- **Other:** Saturn sign-ingress dates move by up to ~17 min; Tajaka solar-return instants unchanged; no class flip (sign, nakshatra, pada, KP) anywhere on this chart; every Vimshottari row stays two_pass_verified.
- **For Pravaha:** the '5.0' read (Vimshottari lahiri levels 1–3) keeps lords and row counts, so "refuse if lords or row counts differ" on L1–3 holds. Anything reading level 4 or Kalachakra needs the declared delta, not equality. SETTLED-1 will carry the measured per-system, per-level shift with tolerance and the level-4 deltas.

## Addendum 8 (2026-10-03) — one Swiss-thread helper after S-L1 (agreed with Suvarna)

After the S-L1 window and before the next L1 build (I-21 targeted re-run), converge on ONE helper: panchang_engine/swiss_thread_scope.py (Pravaha's, the lower layer both trees depend on) becomes the single owner; pyjhora_adapter/_swiss_thread_scope.py becomes a thin call into it or is removed; the boundary test's owner set reduces to one entry. Conditions: the kept helper pins the .se1 path and probes the backend fail-closed on the calling thread (as ensure_swiss_backend does), selects the mode on every call, and both teams' fresh-thread Linux tests and the shared reference value (Sun, Lahiri, JD 2451545.0 = 256.5156961838706°, 1e-9) pass unchanged. Lands after the window because it moves writer digests by import closure. PR shape to be proposed by Pravaha when Suvarna confirms.

## Addendum 9 (2026-10-03, Suvarna) — scheduling terms ACCEPTED

Suvarna ACCEPTED Pravaha's (a)/(b)/(c) answers for 1204/1206/1232/1233/1240/1241 v7: no conflict with their W1 migrations or with S-L1. Terms: the protected train (first merge through the owner's dispatch completing) runs BEFORE their W1 merge and ENDS before it, or after SETTLED-1 — never across their window (the FK to public.charts(id) takes a brief lock on charts). **1241 is applied after SETTLED-1.** The set-up sitting (no schema change) may run any time. Pravaha sends start and end times once the owner confirms; Suvarna posts the W1 slot at least 6 hours ahead. Pre-S-L1 capture: in the hour before their window start, one short read-only transaction, connection closed before their window-start message; never during the window (fallback: their W0 baseline in SETTLED-1).
