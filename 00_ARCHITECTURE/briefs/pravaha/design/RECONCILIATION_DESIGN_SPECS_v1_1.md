---
artifact: RECONCILIATION_DESIGN_SPECS
canonical_id: RECONCILIATION_DESIGN_SPECS
version: "1.1"
status: COMPLETE
date: 2026-09-30
author: "Stream B (Śāstra) — Kimi Code session, campaign/pravaha"
scope: "B3.8 — dispositions of BOTH round-2 reviews (Kimi K3 v1.1: FREEZE_WITH_AMENDMENTS / ACCEPT_WITH_AMENDMENTS; Codex Astra v1.1: REWORK / REWORK) against specs v1.1 (6d08d29e…), oracles v1.1 (6eb25546…), protocol v2.0, registry v2.0, baseline v2.0"
supersedes: "design/RECONCILIATION_DESIGN_SPECS_v1_0.md (B3.6, round 1)"
produces: "design/GOCHARA_DESIGN_SPECS_v1_2.md (5bfe1553…), design/GOCHARA_TEST_ORACLES_v1_2.json (c11a9d7e…), measurement/EVALUATION_PROTOCOL_v2_1.md (21de5994…), measurement/EVENT_REGISTRY_v2_1.md (ec738020…), measurement/BASELINE_3_0_v2_1.md (b4c46222…)"
rule: "every finding is dispositioned accepted / amended / refuted-with-evidence / deferred. A reviewed file is never edited; all changes land in the next version (steward B.8 rule)."
---

# Reconciliation v1.1 — round-2 reviews (B3.8)

Inputs read in full, unedited, committed at f960cbc7b:
KIMI_K3_REVIEW_DESIGN_SPECS_v1_1.md (`15383da2…8468`) and
ASTRA_REVIEW_DESIGN_SPECS_v1_1.md (`22e9b314…6aca`).

## 1. Kimi K3 round-2 findings

| id | finding | disposition | where closed |
|---|---|---|---|
| NK-1 (BLOCKING) | Registry omits EVT.2015.XX.XX.01 (SPR.D); header arithmetic double-counts CURRENT.01; consequences: 47 held-out, re-run, floor restate | **accepted** | EVENT_REGISTRY_v2_1 §3 row 41 (SPR.D, LEL:1766); header now **57 = 3 dev + 47 held-out + 7 excluded**, CURRENT.01 inside the 7, counted once; BASELINE_3_0_v2_1 re-run (T-cover 32/47; SPR.D is a hit — spiritual_turn is an era class); floor restated floor(30/2)+1 = **16** (protocol v2.1 §6.3) |
| NK-2 (BLOCKING) | Identity tuple lacks an occurrence/time component — a retrograde re-crossing collides | **accepted** | specs v1.2 §6.1: `contact_id = hash(physical_object_id, occurrence_ordinal)` over the ordered crossing set (full-precision t_exact ordering, rounded-time hashing forbidden); oracle **O-RX-1** (three crossings of one tuple) |
| NK-3 | Declare contact_id + generation in §1.1; fix record_id natural key | **accepted** | specs v1.2 §1.1: `contact_id` FK (NOT NULL on transit rows, NULL on natal-fact rows), `generation` NOT NULL; natural key extended with `prerequisites` and `source_text` |
| NK-4 | Pin the within-path score algebra, one sentence, null propagation | **accepted** | specs v1.2 §2.1: per-path score = **product** of factor scores; missing operand takes declared `null_state` (`omit` drops, `unqualified` propagates); never 0/1 by default; cross-path stays max |
| NK-5 | Baseline dedup narrative wrong: 10 decade candidates per era class, not 1 century candidate; foreign_settlement 20 | **accepted — verified at source** | recomputed from the pinned extract (914 rows): era classes 10 rows → **10 merged candidates** (non-abutting decades); foreign_settlement 30 → **20**; full per-class table now printed in BASELINE_3_0_v2_1 §1 (the v2.0 sentence is corrected there with the finding cited) |
| NK-6 | Scorer: real hit-day computation for T-FP; signed-intensity ranking | **amended** | signed-intensity ranking accepted (scorer v2.1: si descending both valences, convention asserted: adverse rows carry positive si). The hit-day repair is **superseded by R2-M02's chosen estimand** — T-FP is now all-observed-time admitted day-fraction vs budget on one denominator H (protocol v2.1 §6.4); with the estimand unified, a separate hit-day term has no role. Adjudication stated in §3 below |
| NK-7 | O-SM-1, O-SM-2, O-RR-5, O-PP-2 not literal; O-VI-2/4, O-SS-2/3 falsely labelled literal | **accepted** | oracles v1.2: O-SM-1 (full synthetic station formula printed with expected values), O-SM-2 (δλ 1.8° / orb 1.5° / margin 1.4° printed), O-RR-5 (pinned yoga, class, strength 0.8, cancellation, both fixtures), O-PP-2 (both periods quoted verbatim from L1 chart_dashas with the relationship chains); O-VI-2/O-VI-4/O-SS-2/O-SS-3 given literal timestamps; new explicit **`fixture_kind`** field (`literal` / `constrained_generator`) on all 57 oracles so no generator masquerades as literal |
| NK-8 | §6.4 derivation sentence: declared allowance presented as derived | **accepted** | protocol v2.1 §6.4: the ±45 d footprint, factor-3 slack, 90 d window, n_c=0 allowance are restated as **declared engineering allowances** (policy chosen so blanket-claim classes fail by construction); the v2.0 derivation sentence is withdrawn (registry v2.1 §5 carries the same statement) |
| NK-9 | Percentile asymmetry: misses at 100 vs max real 100(r−1)/N | **accepted** | protocol v2.1 §4.4 states the asymmetry explicitly (a miss at 100 is strictly worse than any real rank; convention kept deliberately) |
| NK-10 | Grandfather controls drawn at 365 d; should be the 61 d interval | **accepted** | controls regenerated (random_controls_v1_1.json, sha256 05539e85…): every event drawn at its own resolution (exact 1 d, month 30 d, year 365 d, interval = its own length — grandfather 61 d, 2026.01 59 d); `randrange(0, H−span+1)` inclusive fix (also R2-M05) |
| NK-11 | EVT.2004 (year-grain edu) is a HIT — "miss every event" false; 15/16 | **accepted — verified** | scorer v2.1 prints instant-class tally: **15/16 miss; hit = EVT.2004.XX.XX.02**; BASELINE_3_0_v2_1 §2 corrected with the finding cited |
| NK-12 | G-10 also blocked O-BP-1/O-BP-4 | **moot — resolved** | extracts landed (G-10, §5 below): O-BP-1 now cites extract v1_0 operands (tier single_pass verbatim); O-BP-4 remains a constrained generator pending the donor rebuild, labelled as such |
| NK-13 | birth_anchor rows = O-CF-N6 would fail '3.0'; disclosure | **accepted** | '3.0' emits birth_anchor rows (base 99.87 %, degenerate-high) — disclosed in BASELINE_3_0_v2_1 §3's all-class two-horns tally (22 high includes birth_anchor); O-CF-N6 stands as the candidate-side guard for future generations |

Kimi's question answers (recorded, verified): the one overridden round-1 finding was correctly
recorded as such; 51/55 oracles were buildable-as-written (the 4 exceptions are NK-7's, now
literal); both registry judgment calls (2026-03-20 → major_gain remap; MBA enrolment
restoration) were judged correct — both retained in registry v2.1; the instant-class
settlement was verified with exactly the two corrections Kimi named (NK-11, NK-13), both
applied; the budget arithmetic was verified — kept unchanged in v2.1.

## 2. Codex Astra round-2 findings

### 2a. Spec findings

| id | finding | disposition | where closed |
|---|---|---|---|
| R2-S01 | Typed contract gaps: contact_id, generation, version-bound FKs, tagged nulls, signature-house role | **accepted** | specs v1.2 §1.1: `contact_id` + `generation` columns with null rules (tagged nulls); `object_role` gains `signature_house`; FKs remain version-bound via `rule_version` on every row |
| R2-S02 | Episode identity must be separate from object/family identity | **accepted** | specs v1.2 §6.1 occurrence identity (contact = object + occurrence ordinal); record natural key extended (NK-3); O-RX-1 |
| R2-S03 | Score algebra underdetermined; O-RP-2's unconditional "NO P4" contradicts the expanded father target set | **accepted** | algebra pinned (NK-4); O-RP-2 rewritten scoped to the **actual father target set** (9th house Sagittarius + its lord Jupiter) with the joint-influence arithmetic written out (Jupiter's aspects from Scorpio miss Sagittarius; the lord contact is Jupiter-self, not Jupiter+Saturn); specs v1.2 §2.2 P4 carries the same scoping sentence |
| R2-S04 | AV comparator "sign's own count baseline" undefined; P5a–e availability matrix; O-BP-5 mutation must cross a band; G-10 payload | **accepted** | specs v1.2 §2.2: P5a comparator = the doctrine's stated expectations only (more/fewer/known-zero — no baseline term); **P5 availability matrix** added as data; extracts v1_0/v1_1 pinned (§5 below) answering the payload request incl. piṇḍa/reduction provenance; O-BP-5 fixture now **crosses a band** (measured 24 → adverse vs config 28 → medium); O-BP-1 carries a competing-values mutation (SAV 32 / Jupiter-BAV 5 / Mars-BAV 0) |
| R2-S05 | O-RP-5: distinct scored-8th-house vs testimony-Sade-Sati fixtures; the v1.1 fixture is 12th-house | **accepted** | O-RP-5 split: **O-RP-5a** (scored: Saturn 172.00° Virgo = 8th from the 327.06° Aquarius Moon, count written) and **O-RP-5b** (testimony: the v1.1 12th-from-Moon Sade-Sati fixture, zero score effect asserted bit-identically); specs v1.2 §2.4 matches |
| R2-S06 | Many fixtures placeholders; O-AD-4 "90° Gemini" wrong | **accepted** | O-AD-4 label corrected to **Cancer 0°** (numeric root 90° unchanged); fixture_kind labels + literals per NK-7; O-SM-3 and O-AO-2 gained **positive controls** (non-empty-set assertions) |
| R2-S07 (round-1 residue) | Oracle fixtures/controls | **accepted** | subsumed by NK-7/R2-S06 closures above; O-AO-1/O-CF-N5/O-CF-N6 already carried real fixtures or non-empty controls from v1.1 and keep them in v1.2 |

### 2b. Measurement findings

| id | finding | disposition | where closed |
|---|---|---|---|
| R2-M01 | Registry: EVT.2015 missing; 3 date grains downgraded; 2002 vertigo labelled onset but LEL records the peak; 56 vs 57 IDs | **accepted** | registry v2.1: SPR.D restored; 2025.06/2025.11 month-grain, 2026.01 interval [2026-01-01, 2026-02-28] (all three timing-usable); vertigo note corrected (peak-not-onset, class retained, grain year); arithmetic 57 = 3 + 47 + 7 |
| R2-M02 | T-FP three incompatible definitions; prediction-dependent mask; recommends all-observed-time per-class burden with matching denominator | **accepted** | protocol v2.1 §6.4: **one estimand** — per-class admitted day-fraction (union of admitted days) ÷ H = 10,334 vs budget 3·n_c·90/H; the v2.0 negative-days mask and v1.x forms are withdrawn; scorer v2.1 implements exactly this |
| R2-M03 | Degeneracy exclusions not implemented → valid T-rank is 0/27 not 1/27; peak-diversity test regressed | **accepted** | protocol v2.1 §8 runs degeneracy **before** rank and excludes degenerate classes from N/floor; peak-diversity restored verbatim (v1.1 §B.1) as §8.3; scorer v2.1: **0/30 eligible → rank-unproven** (all 30 events sit in two-horns classes) |
| R2-M04 | Interval-event N over event year not interval; signed intensity not abs; merge-rep/percentile/aggregation unstated | **accepted** | protocol v2.1: N over the event's start year (§6.3); signed-intensity ranking with the asserted extract convention (§4.3); ties average rank (§4.3); aggregation stated once: T-cover/T-time/T-rank event-pooled, T-FP per class (§9.5); merge representative = max-si member (scorer, disclosed) |
| R2-M05 | Control resolution matching; 61 d grandfather; randrange off-by-one | **accepted** | controls v1_1: matched resolutions, interval-length draws, `randrange(0, H−span+1)`; materialised with seed 482012 (645/940 = 68.6 %) |
| R2-M06 | Coverage manifest absent → T-honesty UNVERIFIABLE; class universe/polarity table; annotation guard not implemented in the scorer | **accepted** | protocol v2.1 §6.5: T-honesty declared **UNVERIFIABLE** without a computation-coverage manifest; the manifest is a **build requirement** for future generations (not a scorer fix); class polarity fixed by the class universe (§2); annotation guard disclosed as manual for this pinned re-run (registry hand-built from LEL anchors + reconciliation), machine enforcement a build-contract item; scorer's hard-coded registry disclosed (machine-readable registry likewise a build-contract item) |
| R2-M07 | Baseline narrative overstatements: "exactly equal" → "no observed separation"; two-horns recount | **accepted** | BASELINE_3_0_v2_1: "no observed separation in this diagnostic"; two-horns recounted over **all 27 classes incl. birth_anchor: 22 high / 5 low / 0 in-band** (matches Astra's expected recount); instant-class statement corrected (NK-11); NK-5 dedup table corrected |

### 2c. Codex's question answers and the two "undocumented departures" (Q1)

Codex Q1 flagged two departures from v2.0 that arrived without an amendment record: the T-FP
estimand change and the peak-diversity regression. **Adjudication:** both are accepted as
protocol amendments and are now documented as such — protocol v2.1's header names both
round-2 reviews as seen, §6.4 withdraws the v2.0 estimand explicitly, and §8.3 restores
peak-diversity with its provenance (v1.1 §B.1). The departure was process, not substance;
the record is repaired here and in v2.1's amendment_disclosure. Codex's remaining question
answers (registry judgment calls, oracle buildability, budget arithmetic) agree with Kimi's
and are recorded in §1 above.

## 3. Contested-point adjudications (reviewer vs reviewer, or reviewer vs prior decision)

1. **T-FP estimand (NK-6 hit-day repair vs R2-M02 all-observed-time):** R2-M02's form adopted.
   Reasons: one estimand with one denominator removes the prediction-dependent mask both
   reviews objected to; the hit-day term is not identifiable at year grain; the budgets were
   verified arithmetically by both reviewers and are unchanged. NK-6 is dispositioned
   *amended*, not rejected: its ranking half landed.
2. **Miss percentile (NK-9):** the worst-rank convention is retained with the asymmetry
   stated, rather than re-anchoring misses at 100(N−1)/N — changing the anchor would move
   v2.0's history out of comparability for no information gain; the convention is disclosed.
3. **P5c disable reason (steward correction, 2026-09-29):** "donor rows pending a
   native-authorised ga_strength rebuild (writer merged in #2731)" — NOT "no L1 source".
   Carried verbatim in specs v1.2 §2.2/§8.1 and O-BP-2.
4. **D-PG353 (native ruling 2026-09-29 18:09 UTC):** the generalised PG353 attenuation stays
   removed unless a cited rule supports it; specs v1.2 §5.1 cites the ruling (the "pending
   ruling" language is gone).
5. **Reviewed-file rule (steward B.8):** v1.1 specs/oracles/packet restored to 0471400ce
   bytes (verified 6d08d29e / 6eb25546 / 145f7b1b against the reviews' frontmatter); all
   round-2 changes land in v1.2/v2.1; the G-10 extracts are new files, not mutations.

## 4. Self-found item (not from either review — disclosed, deferred to the third round)

**B38-F1 — O-PP-1's expected periods do not match L1 chart_dashas.** While pinning O-PP-2's
literal periods from `chart_dashas` (system_id = 'vimshottari'), the level-2 rows give:
2013-12-11 → **Mercury/Sun** (2013-04-23 → 2014-02-27), not Mercury/Ketu as O-PP-1 asserts
(Mercury/Ketu ran 2009-06-26 → 2010-06-23); 2018-11-28 → **Mercury/Rahu** (2016-07-26 →
2019-02-12), not Mercury/Moon; 2022-01-03 → **Mercury/Saturn** (2021-05-20 → 2024-01-28),
not Mercury/Rāhu. Vimśottarī AD order inside one MD is arithmetic, so no ayanamsha variant
explains the discrepancy. O-PP-1's expected values were inherited from the v1.0 specs and
passed both review rounds. **Disposition: deferred** — flagged for the narrow third round
(and the native) as a probable defect in O-PP-1's `then` values; the oracle IDs and the
assertion structure (exact MD/AD/PD, no hard-coded PD) are unaffected. Not silently fixed
here because O-PP-1's expectations were review-accepted twice; the fix should be
review-visible.

## 5. G-10 evidence (native routing, steward addendum — both closed)

- `design/L1_ASHTAKAVARGA_EXTRACT_v1_0.json` (`312de09e…88fe83`): 96 BAV+SARVA rows,
  lahiri_chitrapaksha, build aa9602ce (the frozen t0 ga_strength build), fact_ids,
  engine pyjhora/1.0.0, tier `single_pass` carried verbatim; independent pyjhora recompute
  from graha_position build 1c092ffb longitudes matched **all 96 rows** — the build-identity
  question (aa9602ce vs 1c092ffb) is answered by recompute, not assumed.
- `design/L1_ASHTAKAVARGA_EXTRACT_v1_1.json` (`e9e5d4d3…3224`): 200 rows — trikoṇa śodhana 84,
  ekādhipathya śodhana 84 (identical per row in this chart), piṇḍa bhinna/raasi/sodhita/sarva
  32; recompute matched trikoṇa 84/84 and all 21 per-planet piṇḍas; **`pinda_sarva`'s
  per-subject split is NOT recompute-covered** — the flag persists in specs v1.2 §2.2/§8.1.
- Donor-level rows: 0 in L1; writer merged in PR #2731 (migration 1086); rebuild deferred by
  the native ⇒ P5c disabled with the rebuild-pending reason (§3.3).

## 6. Artifact hashes (full sha256)

| artifact | sha256 |
|---|---|
| KIMI_K3_REVIEW_DESIGN_SPECS_v1_0.md | 7872f239d0127e48fbd2d20b1c1a52fde8ca69f1f078c6acfb244871f8e7c8c7 |
| ASTRA_REVIEW_DESIGN_SPECS_v1_0.md | 536d2b1a0d50a733b3cdf0ab4f97fc9328c988cc67b5611a1a6c5e17a2b0a8ee |
| KIMI_K3_REVIEW_DESIGN_SPECS_v1_1.md | 15383da2f6aca9944594c7b021a1e7a8245cf3167ae422028dc2542b949e8468 |
| ASTRA_REVIEW_DESIGN_SPECS_v1_1.md | 22e9b31485df87f5217622fea1de17a40e48623abc461163f0cd0148beb76aca |
| GOCHARA_DESIGN_SPECS_v1_1.md (restored, history) | 6d08d29e8fff03cd2841c12b547a0eae1e9be77702942286a6c2a09adfdb0942 |
| GOCHARA_TEST_ORACLES_v1_1.json (restored, history) | 6eb255460d83800d2c1cab755345bece46e462bd7fe11fb9ac89f2f429a3de05 |
| REVIEW_PACKET_DESIGN_SPECS_v1_1.md (restored, history) | 145f7b1b2a4de9930ed8d866fbfbd1fd0aaa240e43498e7362bc619f608ef716 |
| L1_ASHTAKAVARGA_EXTRACT_v1_0.json | 312de09e791e34e58377b7c0956e39f6691490bd2cfd0a27b415a7055c88fe83 |
| L1_ASHTAKAVARGA_EXTRACT_v1_1.json | e9e5d4d3f48c0588036d0e837eb3d5077e0e2f85e7da22c1ac866f131a5c3224 |
| **GOCHARA_DESIGN_SPECS_v1_2.md** | 5bfe1553d404be59f9b0246fcf410fe5a09be6946b5d97da6d733ecede45b039 |
| **GOCHARA_TEST_ORACLES_v1_2.json** | c11a9d7e5ccf3a6c4a53569da5383ea7531ce840e48cfa6f7e0b8e2310143a43 |
| EVENT_REGISTRY_v2_1.md | ec738020dd2fbbe492317089a8ac5723169756740de932cea408aeb5cde7f34c |
| EVALUATION_PROTOCOL_v2_1.md | 21de59943b335abb3df393810155c2a0d07315c5b1ae7fee5d54e93e7f5c7f1d |
| BASELINE_3_0_v2_1.md | b4c46222fe23fbd51b5028004d11a11cfafb422de124c23c4f4867bfb8a4ce60 |
| rerun_3_0_v2_1_scorer.py | c3d567320bdce07c0516f9dc07e01d41043074b12ec511ba0198b56ad4d37228 |
| random_controls_v1_1.json | 05539e8585e99b6493641fa637d6531e5605bf36e62c0aacb1c2f1f4279a5103 |
| rerun_per_event_v2_1.json | 58600054d3ed74b8ffee08aa60a7852f4e9f755edb8abbf16131180ee17b1e27 |
| baseline_3_0_extract_v1_0.json (pinned, unchanged) | 70ba61421915db2ec3fcf3d1a23bc0ad80d43055b0d0bcc656e5a89079ef84ff |

*End of reconciliation v1.1. Nothing herein sets status: FROZEN anywhere; the native decides
whether v1.2/v2.1 return to review before D-SPECS / D-PROTO. No reviewer was dispatched.*
