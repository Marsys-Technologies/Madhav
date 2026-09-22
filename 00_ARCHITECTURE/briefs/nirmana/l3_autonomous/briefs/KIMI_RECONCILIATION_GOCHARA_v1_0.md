---
artifact: KIMI_RECONCILIATION_GOCHARA
version: "1.0"
status: CLOSED (one row re-opened and re-disposed 2026-09-23 — M-3; see its cell and the plan's 2.1b changelog)
date: 2026-09-23
reviews: KIMI_K3_REVIEW_GOCHARA_v1_0.md (Kimi K3, effort=max, generated 2026-09-23T02:00 IST, 56,291 bytes; verdict PROCEED WITH AMENDMENTS — 3 blocking, 6 major, 7 minor)
reviewed_document: GOCHARA_FAMILY_ELEVATION_PLAN_v2_0.md (pre-2.0a text as read by Kimi; 2.0a amendments from the Kṣetra session were additive and are carried into v2.1)
produces: GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md (the final plan handed to the L3 elevation; still PROPOSED_FOR_NATIVE_RULING)
method: "Every finding that asserts a code, data or corpus fact was re-verified at source or live before disposition. Labels: VERIFIED (re-checked here) · ACCEPT · ACCEPT-AMENDED (accepted with a stated change) · TO-NATIVE (accepted as a ruling item, not adopted unilaterally) · REJECT (with reason)."
---

# Reconciliation of the Kimi K3 review — Gochara family plan v2.0 → v2.1

## 1. Disposition table

| # | Kimi finding | Verification here | Disposition | Plan v2.1 delta |
|---|---|---|---|---|
| **B-1** | `clear_tables` is read nowhere in the Clear routes; only Atlas display reads it; §6.3/§6.4's cleanup claim is wrong; ledger/coverage would be orphaned by every Clear | **VERIFIED**: readers are `atlas/schema/route.ts:19`, `AtlasView.tsx:33-35`, `atlas/page.tsx:17` only; `execute/route.ts:160-183` resolves `EXPLICIT_CLEAR_OPS` → `count_sql` → `target_table` | **ACCEPT** | F-24; §6.3 row replaced by an `EXPLICIT_CLEAR_OPS['ka_gochara']` entry with three generation-scoped DELETEs (`clear_tables` kept for Atlas display only); §6.4 rewritten; §10 Clear-proof row; N-9 (iv) |
| **B-2** | `GocharaTransitService.find_aspects` has consumers beyond Saṅgam: `kala_trigger/trigger.py:87,96,150,199` and `scripts/kala_admission/currents.py:59`; S-1 as written breaks them | **VERIFIED** at the cited lines | **ACCEPT** | F-25; §6.1 rows; S-1 keeps `find_aspects` shape-compatible (adapter over episodes) and adds `find_episodes`; new packet T-1 (kala_trigger owner); §10 row |
| **B-3** | H-1 as stated repairs the citation, not the astrology: kakṣyā divisions are equal eighths by doctrine; L1's 120 rows need explaining; the primitive never bindu-qualifies; saturation persists | **VERIFIED**: L1 `ashtakavarga_kakshya_boundary` = 8 subjects × 3 keys (`lord/start_deg/end_deg`, 0…26.25 / 3.75…30) per ayanāṃśa — the same equal-eighths grid, sign-relative; `primitives.py:686-691` reads `start_deg` only; L1 holds BAV totals per sign/house (`ashtakavarga_bindu_sign` 96, `ashtakavarga_bindu` 96) but **no per-contributor matrix**; corpus has no kakṣyā passage (grep `kaksh` → none) | **ACCEPT-AMENDED** | H-1 split: **H-1a** provenance (fixture → L1 grid; does not fix saturation — stated); **H-1b** unqualified kakṣyā crossings contribute no activity (`completeness_state=unqualified`) — put to the native as **N-13** because it changes served λ; **M-7** bindu-qualified kakṣyā scoring (method); **G-10** L1 per-contributor BAV matrix gap; F-27 citation not corpus-verifiable |
| **M-1** | Clear of the authoritative `'4.0'` leaves authority + `published` manifest pointing at a void | reasoning verified against §4.7/§6.4 | **ACCEPT** | Clear refuses when target generation is authoritative unless the release authority cascades an authority reset + manifest `cleared`; integrity conjunct (k) |
| **M-2** | Hardcoded `'4.0'` branch breaks on `'4.1'` | verified against `register_gochara_windows.ts:573-598, :966` | **ACCEPT** | P-1a/P-1b manifest-driven; string branches only for `v1`/`3.0`/`g3_*` |
| **M-3** | Corpus lacks Phaladīpikā, Sārāvalī, Bṛhat Saṃhitā, JP, Praśna Mārga, UK; Moorti doctrine absent; Sade-Sati only in KP vol. 5 | **REFUTED 2026-09-23 — and my "VERIFIED" here was the same error.** I confirmed the reviewer's claim against the source-data *directory*; the served corpus is `classical_text_chunks`, 15 texts / 10,651 chunks, and **Phaladīpikā is in it** (564 chunks, 17 vedha; Adh. XXVI at `PG322/323/339/347-349`) `[L]`. The reviewer, the Kṣetra session, the strategic session and I all made the identical directory-for-corpus error independently | **REJECTED on the premise; the sub-findings that do not depend on it stand** | G-9 **inverted**: re-cite the 41 rules against Phaladīpikā Adh. XXVI rather than admit-or-permanently-flag; §5.4's `corpus_verifiable` rewritten; the uniform `unqualified` adopted by the Kṣetra and Saṅgam sheets flagged to their owners as resting on my wrong premise; M-8 upgraded to verse-cited (`PG322:C1` Sun–Saturn, `PG323:C1` Moon–Mercury); F-29 re-graded UNVERIFIED not absent; new F-32 makes a `count(*)` against `classical_text_chunks` the only admissible basis for an absence claim. Full account: plan changelog 2.1b |
| **M-4** | Century writer is `@register`ed, active, dual-writes `'3.0'`; hold is procedural; after the guard its prod write crashes | **VERIFIED**: `@register` `:1717`; `DELETE FROM {PROD_TABLE}` `:2257`; `is_active=true` live | **TO-NATIVE** (lifecycle change) | **N-6a**: set century `is_active=false` at guard time, reversible, nothing deleted; post-guard prod write fails loudly by design (stated in §9) |
| **M-5** | Moon on-demand searches never enter the coverage manifest | reasoning verified | **ACCEPT** | `moon_on_demand` partition rows written/derived per requested interval; P-4 exposes `searched_horizon` |
| **M-6** | Value row and WP4 depend on artifacts not on main; gate WP0/WP1 | **VERIFIED** (only in `setup` worktree) | **ACCEPT** | WP0/WP1 exit gate; CI-enforced NOT_RUN |
| m-1 | Spike used tropical−ayanāṃśa, uncommitted | true (App. C) | ACCEPT | WP3a gate: commit as test; re-run under `FLG_SIDEREAL`, `retflag 258` + checksums |
| m-2 | E8 classes not in spike | true | ACCEPT | App. C scope note; WP3a on real arcs |
| m-3 | tolerance change can shift `t_exact` <60 s with same id | reasoning verified | ACCEPT | tolerance/method change ⇒ new `convention_id`; `method_version` in hash |
| m-4 | arc reuse across charts unstated | true | ACCEPT | §4.2: arcs are global per `substrate_version`; contacts per chart |
| m-5 | transient 0-count between steps 5 and 6 | true | ACCEPT | §9 note |
| m-6 | R-5 missing from WP3c gate | true | ACCEPT | added |
| m-7 | sign discrepancy Astra F4 vs brief on the nutation gap | not re-derived here | ACCEPT | WP0 pins the sign convention |
| A-final | writer must refuse delete-then-insert against a `published` generation | consistent with §4.7 | ACCEPT | WP6 gate |
| B.1 | cite BPHS ch.66–72 as doctrinal spine; ch.70 nakṣatra timing; ch.26 ślokas 6–8 dṛṣṭi-koṇa as warrant for graduated strength | ch.26 6–8 **VERIFIED** at `bphs_vol1:16514-16529`; ch.66 heading at `bphs_vol2:35553` | ACCEPT | §4.2 doctrine note; M-1 warrant |
| B.1/B.4 | vedha exceptions (Sun–Saturn, Moon–Mercury) and vipareeta vedha are doctrine; `ka_vedha_gochara` implements neither | doctrine **VERIFIED** (`kp_reader_vol5:1341-1343`; `bphs_vol1:24414-24441` incl. the Saturn-in-9th exception); code **VERIFIED** absent (`logic.py` has only `NATURAL_MALEFICS`) | **ACCEPT-AMENDED** | F-26; **M-8** (method, evidence first, strong [D] basis; recommended early) rather than silent WP9 change |
| B.2 | all five §5.3 rules affirmed; M-5 ruling: whole-sign primary, cusp = KP-school variant; E-1 order Gulika/Māndi → bhāva-ārūḍhas | Gulika rule **VERIFIED** `kp_reader_vol5:1735-1741` | ACCEPT as recorded recommendations | §1.4 M-5/M-6 recommendation text |
| B.3 | N-4 approve; N-4a amend to (b′) direct Swiss `MEAN_NODE` — reads my (b) as a "regression model" | (b) never meant regression: "analytic" = Swiss mean-elements node | **ACCEPT-AMENDED** | N-4a restated as **(b″)**: `swe.MEAN_NODE` under `FLG_SIDEREAL`, one L0-owned implementation (Kṣetra placement rule), knots untouched, no rebuild — wording fixed so it cannot be read as regression |
| B.4 | H-6 before/after λ at WP5; Sade-Sati phases as qualifiers; no retrograde weight; tārā citation check; latta after G-9 | reasoning verified | ACCEPT | WP5 gate; **E-2** Sade-Sati qualifier; §8 notes |
| B.5 | Moorti at true ingress; Vedha independence_group; Kota gate — affirmed | — | ACCEPT | none |
| C.1 | commit spike; FLG_SIDEREAL; E8 on real arcs; Moon sweep; `near_station_unresolved` → `completeness_state`; per-relation tolerance floors | — | ACCEPT | §4.2, WP3a |
| C.2 | overlay-at-instant proof; `comparable_with` vocabulary pinned; `moon_on_demand` marker; indexes + latency | — | ACCEPT | §4.3, §10, WP1/WP4/WP6 |
| C.3 | content digests for small reference tables; orb table and kakṣyā lord order must be sourced | — | ACCEPT | §5.5, WP1 |
| C.4 | add `bg_transit_rules` to `depends_on`; registry linter: no `kala_gochara_windows` asset without a generation predicate | — | ACCEPT | §6.3; N-9 (v) |
| C.5 | post-rollback Kṣetra edges note | — | ACCEPT | §9 |
| C.6 | CI-enforced NOT_RUN; independent oracle for the duplication row; #2534 fixture; Clear proof | — | ACCEPT | §10 |
| C.7 | cost profile must price kernel arc-build/solve, ledger write/index, end-to-end vs 58.2 min; never vs 20–25 h | — | ACCEPT | §4.5, §1.6 |
| D | enrichment ranking 1–9 | — | ACCEPT as recorded | §1.4/§5.3: 1→M-7+G-10, 2→M-8, 3→E-2, 4–5→M-6, 6→G-9; 7–9 wait |
| E | N-1..N-12 approvals with conditions; M-1 rule first after M-5; M-2 defer; M-3 Moon as a separate channel; M-4 approve; M-5/M-6 as above | — | recorded for the native | §1.3 "reviewer recommendation" column |

**Rejected:** one, added 2026-09-23 — M-3's corpus-absence premise, which I had wrongly confirmed. See the plan's 2.1b changelog. Two further premises were corrected rather than rejected (N-4a "regression"; M-3's `uncited_extension` label, now moot). Two premises were corrected rather than rejected (N-4a "regression"; M-3's `uncited_extension` label).

## 2. What the review did not change
The kernel/ledger/coverage/publication architecture, the runbook order, the target-resolution contract, the ratified D/R decisions, and every 2.0a amendment (Kṣetra alignment) stand. Kimi found no contradiction with D-1..D-3 or R1–R10 and confirmed N-1 is disclosed as a proposal.

## 3. New items the review surfaced that are the native's, not mine
N-13 (H-1b changes served λ), N-6a (century `is_active`), M-7/M-8 (method), G-10 (L1 gap), and the widened G-9 (corpus ingestion). Each is in v2.1 §1.3–§1.5 with Kimi's recommendation beside mine.
