---
artifact: GOCHARA_PLAN_V3_AMENDMENT
canonical_id: GOCHARA_PLAN_V3_AMENDMENT
version: "1.0"
status: CURRENT
date: 2026-09-29
author: "Stream B (Śāstra) — Kimi Code session, campaign/pravaha"
authority: >
  Written under B3.1 after D-BRIEF (native, 2026-09-29: the sealed FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0.md
  is countersigned as the Gochara final brief). This amendment RECONCILES; it changes no ruling, seals nothing,
  and authorizes no build. Where plan v2.1 and v3.0 conflict, v3.0 governs the doctrine and the Pravāha campaign
  plan governs the execution sequence; the conflicts are named, not smoothed over.
reconciles: >
  GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md (NATIVE_RATIFIED_PLAN, lane branch l3/gochara-autonomous-wp0-7) +
  GOCHARA_RULING_SHEET_v2_0.md + GOCHARA_NATIVE_RULINGS_2026-09-24_v1_0.md + ADHIKARIN_RULINGS.md (ADK-0001..0028)
  AGAINST sealed/FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0.md and PRAVAHA_CAMPAIGN_PLAN_v1_0.md.
---

# Gochara — plan v2.1 ↔ v3.0 amendment v1.0

## 1. Rulings that stand untouched

v3.0 §3 says it directly ("Kept exactly as ruled"), and the 2026-09-29 decision round (D-RQ1…D-RQ8,
D-P4, D-PADMIT — all ruled "accept all recommendations") closed every ruling request v3.0 carried.
The following ratified rulings are **untouched** and bind all Pravāha work:

| Ruling | Content | v3.0 position |
|---|---|---|
| D-1 | (plan v2.1 §1.3) family decisions as ruled | kept |
| N-4 / N-4a | mean-node derivation owned by L0's ephemeris service; `node_mode`/`epoch_convention` declared on the row; no consumer-side copy (§N.5) | kept |
| N-7 | contact object persisted as `kala_gochara_contacts`, owned by `ka_gochara`; this stream produces Saṅgam's directed events (Saṅgam M-3 at 101046052) | kept — and now load-bearing for S-2 with the T0-1 aspect fix |
| M-1 | linear-no-box shape ruled; implemented **angularly** (`1 − |Δ|/orb`), 5.0° candidate 1 / 1.0° candidate 2 | kept; defect N1 (time-triangle implementation) is a conformance defect, fixed under T0-9 per D-RQ2 |
| M-2 | no dwell weight; retrograde typed as testimony (pass identity, station, repeated opportunity) | kept (v3.0 P10: testimony, no weight) |
| M-3 | Moon out of the century λ; Moon channel on demand (P6) | kept; D-RQ3 adds the PG321/PG331 Moon-relative node recount (B3.3) |
| M-4 | mechanism audit order before any operand use (Kota `w25` etc.) | kept |
| M-5 | interval-vs-point target semantics (§5.3 contract) | kept; absorbed into the v3.0 relationship record (§2.3) |
| M-6 | derived points scoped; **bhāva-ārūḍhas ranked first** (the KP-vol5 Gulika rule is not in the served corpus — `text_id ILIKE '%kp%'` → 0 chunks); Gulika/Māndi needs its rule re-found in an admitted text | kept with the v2.1 ordering caveat |
| M-7 / N-13 / G-10 | nāḍī kakṣyā rows = MEDIUM testimony, never weight (N-21); per-contributor BAV matrix gap (G-10) | kept; D-RQ1 settles the zero-vs-unresolved distinction: observed-zero favourable marks are doctrinally adverse (BPHS ch.70 vv.24–27), unresolved operand = `unqualified`; bindu/rekhā polarity normalised first (N8); M-7 bands remain a WP8 hypothesis |
| M-8 | vedha exceptions (Sun↔Saturn, Moon↔Mercury), vipareeta cancellation with `cancelled=true` | kept; v3.0 T0-8 adds scoped interval relations + cancellation sub-intervals (N4) |
| N-14 | no nodal dṛṣṭī; nodes stay agents and targets | kept — D-RQ3 explicit: the recount authorises no nodal aspect |
| N-15 | Sade-Sati out of λ, testimony only | kept; D-RQ5 shapes the testimony: phase-split (12th/1st/2nd from the Moon), never on gain classes |
| N-17 | no peak cap | kept; D-RQ6: producer's 90-day filter moves to serve time **now** (N5); the substance is revisited only after Tier 0 |
| N-21 | nāḍī MEDIUM = testimony never weight | kept |
| N-22 | unqualified kakṣyā → no activity, rides first candidate | kept, as modified by D-RQ1's zero/unqualified split |
| ADK-0026 | honest-over-plausible outranks least-change; fix data, not detectors | kept — governs every B4/B5 measurement |
| ADK-0027 | deploy-before-flip; chart-1 `'4.0'` label BURNED; soak trigger #0 | kept — D-41 is its successor (`'4.1'` proof only, `'5.0'` first sound candidate) |
| ADK-0028 | local century enumeration PROHIBITED; Cloud Run job only after #2731 merge+deploy | kept — standing rule 1 of the campaign |

## 2. What v3.0 + the campaign decisions supersede in plan v2.1

These are **supersessions by the native's own later rulings**, recorded so no one executes a stale packet:

1. **N-10's label `'4.0'`** — superseded by ADK-0027 + D-41. `'4.0'` is burned on chart 1; `'4.1'` is
   an engineering proof and geometric baseline, candidate-only, never flipped; the first sound
   candidate is `'5.0'`. N-10's *mechanism* survives intact: per-(chart, generation) publication
   manifest, `ka_gochara` publishes candidates, the release authority flips, **manifest-driven**
   provenance (P-1's test — "passes unchanged after a rebuild republishes" — now runs on `'4.1'`
   then `'5.0'`). The immutability rule is why the label changed; the manifest design is why the
   change costs nothing.
2. **The WP10 production cutover path** (local build → four flip gates → authority flip) — superseded
   by the Pravāha phase map: geometry Tier 0-G before any century build (A2.1–A2.3), century builds
   only as the Cloud Run job under D-CLOUD (A2.5 `'4.1'`, A5.6 `'5.0'`), flip only at J2 under D-FLIP
   after A5.7 gates and B5.4 retrodiction. ADK-0028 makes the local-enumeration half of WP10's
   runbook unreachable in any case.
3. **The twelve-system weighted permission vote** — withdrawn by v3.0 §2.2. Admissibility is a
   **union of source-qualified rule paths**, each intersecting its own prerequisites; Vimśottarī is
   the spine, Chara serves Jaimini targets, Aṣṭottarī's vote is **absent on this chart** (D-RQ7 —
   both BPHS ch.46 conditions fail), Mudda lives inside the annual path, the rest are testimony until
   adjudicated as independent paths. E6's per-class decade-constant permission is the defect, not a
   baseline.
4. **Noisy-OR promise over type-constant weights** — withdrawn (v3.0 finding #1, confirmed by both
   reviewers). Aliases of one physical contact (kāraka / 9L / yoga constituent) are **role edges on
   one observation**, never independent evidence. Promise = strength *and* condition from L1 (§2.5).
5. **The four-level hierarchy as a necessary-condition law** — retained as order of inquiry and
   **computation strategy** (prune only where a necessary predicate of the path is demonstrably
   false; unknown applicability ≠ false applicability). No fixed planet→grain law; era/month/day are
   output resolutions of the paths that operate at those grains.
6. **Sade-Sati / Kaṇṭaka as open licences, sahams in the decade path** — withdrawn; Sade-Sati is
   phase-split testimony (D-RQ5), sahams moved to the annual Tājaka path (P9, Tier 2) with per-year
   object identity.
7. **Chart-2 `'4.0'` candidate rows** — disposition is Stream A's under A0.1/ADK-0029 (D-SCOPE:
   builds for 482012f1 only). No Pravāha item reads them as a baseline; E1 used them only as a
   structural proxy, with the proxy declared.

## 3. v3.0 items that needed new rulings — all ruled 2026-09-29

v3.0 §7 carried eight ruling requests; §2.4 carried two admissions. All ten are **ruled**
(NATIVE_DECISION_PACKET_v1_0.md records each page verbatim):

| Request | Ruling | Consequence for the plan |
|---|---|---|
| RQ-1 (M-7/N-22) | D-RQ1: zero ≠ unresolved; polarity first; bands = WP8 hypothesis | T0-11 + P5 spec |
| RQ-2 (M-1) | D-RQ2: angular kernel now; BPHS ch.26 profile = separate versioned calibration study | T0-9/A5.4; calibration study queued at L5 |
| RQ-3 (M-3/G-9) | D-RQ3: recount PG321/PG331; N-14 stands | B3.3 read list |
| RQ-4 (mūrti) | D-RQ4: rule form unadmitted (0 chunks by predicate); testimony-only; auto `verse_cited` stamp removed | T0-9 (N7 fix); A-1 true-ingress stands |
| RQ-5 (N-15) | D-RQ5: phase-split testimony, never gain classes | testimony row spec |
| RQ-6 (N-17) | D-RQ6: revisit after Tier 0; producer filter to serve time now | T0-9 (N5 fix) |
| RQ-7 (Aṣṭottarī) | D-RQ7: vote absent (both conditions fail); B3.3 confirms the pakṣa operand | permission spec |
| RQ-8 (citations) | D-RQ8: KP-vs-Phaladīpikā Venus-vedha note in `rule_notes`; "§double-gochara" struck for `[P]` + PG216 | seed hygiene (L0 owner); P4 spec |
| P4 double transit | D-P4: admitted `[P]`, `uncited_extension`, house-or-lord / occupation-or-aspect | Tier 1 path |
| other `[P]` | D-PADMIT: testimony first; weight only after ablation | B5.4 attribution feeds any promotion |

**Open future ruling points** (not yet due, named so they cannot arrive by stealth): D-SPECS at
B3.6 (freeze) · D-FLIP at J2 · D-T2 at J2 (path-by-path Tier 2) · N-17 substance after Tier 0
(D-RQ6) · M-7 band calibration at WP8 (D-RQ1) · any `[P]`→weight promotion after B5.4 ablation
(D-PADMIT).

## 4. Packet disposition — what survives, what is absorbed, what is stale

| Packet | Disposition |
|---|---|
| **P-1** (`register_gochara_windows.ts` provenance/coverage, manifest-driven, no `'v1'` COALESCE) | **Survives.** Now a J2 flip gate under D-FLIP; its "republish as `'4.1'`" test runs on `'4.1'`→`'5.0'`. Stream A scope |
| **P-2** (`reading_checklist.ts` — contact_ids, completeness_state, §N.6 confirmed/context split) | **Survives** (Stream A/serving owner) |
| **P-3** (L5 `contact_id` on the claim ledger) | **Survives** — feeds B6.2's L5 hand-off |
| **P-4** (contact-ledger + coverage read capability with `density_contract`) | **Survives** — B4 baselines query read-only through it or SQL |
| **C-1** (`EXPLICIT_CLEAR_OPS['ka_gochara']` + authoritative-generation refusal) | **Survives** (Stream A, A1.3 hygiene) |
| **S-1 / T-1** (`find_episodes` added, `find_aspects` shape kept for duck-typed callers — F-25) | **Survives**; B3.4 carries the coordination note |
| **S-2** (directed contact events for Saṅgam) | **Survives with a precondition**: its directed events are wrong until T0-1 lands (aspect direction `body = target − angle`; Mars 4/8 and Saturn 3/10 mirrored in the shipped code — v3.0 finding #13, both reviewers confirmed with independent arithmetic). Saṅgam consumption of directed events stays gated until the fixed kernel emits them; v3.0's graduated dṛṣṭi (¼/½/¾/full, **specials full** — `BPHS1:16496-16502`) replaces any fractional-strength convention S-2 drafts carry |
| **K-1 / V-1** (Kṣetra/Saṅgam dependency declarations, `'v1'` fall-through removal) | **Survives**; B3.4 |
| **G-9 re-citation** (41 `bg_transit_rules` rows → Phaladīpikā Adh. XXVI) | **Partially done** (production: 36 verse-cited + 6 UNSOURCED node rows per the 2026-09-24 rulings); D-RQ3's recount and D-RQ8's note finish the doctrine half; L0 owns the seed edit |
| **G-R resonance corrections R-1..R-6** | **Survive as T0-12/A5.4** — the map rebuild on positive-result sensitive facts, typed arudhas, live yoga-firing validation, lord resolution, first-root retention, `target_resolution_state` |
| **WP0–WP10 engineering sequence** (local build, WP10 cutover) | **Absorbed and re-sequenced** by Pravāha phases 0–6 (§2.2 above). The §4 architecture — contact ledger, coverage manifest, three objects (geometry / relationship records / evaluated windows), manifest-driven provenance, target-resolution contract — survives as the design baseline the B3.2 frozen specs refine. The WP10 local-build runbook is stale under ADK-0028/D-CLOUD |
| **WP8 deferred method parameters** (D-3) | **Survives** as the calibration queue: M-1 ch.26 profile (D-RQ2), M-7 bands (D-RQ1), N-17 revisit (D-RQ6) — all evidence-first, none pre-admitted |

## 5. Tier 0 / Tier 1 → campaign item map (the merge granularity)

Doctrine elevation items merge **into the existing campaign items**, not as a separate tranche —
one doctrine item → one engineering or measurement item → one detector:

| v3.0 item | Campaign item | Owner |
|---|---|---|
| T0-1 aspect direction · T0-2 0° seam / fabricated ingress · T0-3 residence spans + truncated contacts · boundary table | A2.1 (Tier 0-G, before any century build) | A |
| T0-4 frames on rule selection + resolution · T0-5 lords/occupants/yoga resolution · T0-12 map rebuild (R-1..R-6) | A5.4 + B3.2 `relationship_record` spec | A build, B spec |
| T0-6 per-instant MD/AD/PD permission · N-15 on projection | B3.2 `permission_per_instant` → A5.4 | B spec, A build |
| T0-7 three-field valence · class-relative polarity | B3.2 `three_field_valence` → A5.4 | B spec, A build |
| T0-8 vedha interval relation (exceptions, cancellation sub-intervals, grade keys, battle-scale stamped `uncited_extension`) | B3.2 `vedha_interval_relation` → A5.4 | B spec, A build |
| T0-9 angular M-1 · 90-day to serve time · `birth_anchor` out · mūrti auto-flag off · solver_method + uncertainty | B3.2 `solver_method_uncertainty` → A5.4 | B spec, A build |
| T0-10 tārā key · kakṣyā key · T0-11 bindu/rekhā polarity | B3.2 `bindu_polarity` → A5.4 | B spec, A build |
| T0-13 measurement first (LEL reconciliation; protocol pre-declared) | B4.1 / B4.2 | B |
| Tier 1 rule paths P1–P6 · promise strength+condition · agent nature/maitrī · yoga→event map | B5.1 / B5.2 (after J1), against B3.2 `rule_paths_P1_P6` | B |
| Tier 3 validation (rank within class and year; held-out; ablations) | B4.2 protocol → B4.3/B4.4 baselines → B5.3/B5.4 report | B |
| Tier 2 (P7–P9, P11, P12, varga objects, SBC grid) | B6.1 after J2 under D-T2 | B |

## 6. Limits

This amendment does not edit the sealed text, the lane plan, or any ruling sheet; it does not
authorize a build, migration, deployment, enumeration, or flip; it does not re-open any ruled item
beyond the ten the native ruled on 2026-09-29. Where it cites a production figure, the figure and
its predicate live in `sealed/FABLE_REVIEW_EVIDENCE_APPENDIX_v1_0.md`; where it cites corpus
content, the count and predicate live in v3.0 §8. Predicates, not numbers (DVA Ruling 16).
