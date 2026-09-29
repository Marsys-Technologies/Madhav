---
artifact: RECONCILIATION_DESIGN_SPECS
canonical_id: RECONCILIATION_DESIGN_SPECS
version: "1.0"
status: CURRENT
date: 2026-09-29
author: "Stream B (Śāstra) — Kimi Code session, campaign/pravaha"
item: B3.6
inputs:
  - design/reviews/KIMI_K3_REVIEW_DESIGN_SPECS_v1_0.md (FREEZE_WITH_AMENDMENTS; protocol SOUND_WITH_ONE_CORRECTION)
  - design/reviews/ASTRA_REVIEW_DESIGN_SPECS_v1_0.md (REWORK / REWORK)
steward_ruling: "2026-09-29 — treat both reviews as REWORK; Codex's additional findings were checked at source by the native and hold"
outputs:
  - design/GOCHARA_DESIGN_SPECS_v1_1.md (reworked; NOT FROZEN — re-review decision is the native's)
  - design/GOCHARA_TEST_ORACLES_v1_1.json (full inventory, fixture+mutation per oracle)
  - measurement/EVALUATION_PROTOCOL_v2_0.md (consolidated; supersedes v1.0/v1.1/v1.2-DRAFT)
  - measurement/EVENT_REGISTRY_v2_0.md (row-level, referenced by protocol v2.0)
  - measurement/BASELINE_3_0_v2_0.md (re-run from a pinned extract; v1_0 retained as disclosed history)
---

# B3.6 Reconciliation — every finding from both reviews, dispositioned

Disposition vocabulary: **accepted** (implemented as requested) · **amended** (implemented in
modified form, modification stated) · **refuted-with-evidence** (evidence printed) ·
**deferred** (named successor item) · **overridden** (native/steward directive supersedes the
reviewer's recommendation — recorded, not argued).

The steward pre-ruled both reviews REWORK and confirmed Codex's source-checked findings hold;
the default disposition is therefore acceptance, and every refutation prints its evidence.

## A. Kimi K3 findings

| # | Finding (abbreviated) | Disposition | Where resolved |
|---|---|---|---|
| F1 | Oracle JSON has 25 entries; 14 spec-named oracles absent (O-RP-1, O-TV-2/3, O-PP-3, O-VI-2/4, O-SS-4, O-SM-2/3, O-BP-3, O-AO-2/3, O-RW-2/3) | **accepted** | Oracles v1.1 JSON: complete inventory, count stated, spec §11.2 index = JSON exactly |
| F2 | #13 aspect direction (T0-1) has no invariant and no oracle | **accepted** | Specs v1.1 §6/§7 invariant + O-AD-* directed oracle set first in JSON (target 0° → Mars 4th 270°, Mars 8th 150°, Saturn 3rd 300°, Saturn 10th 90°; rejects the mirrored `target+angle` implementation) |
| F3 | Unguarded: #24 (plateau), #5 (tārā key), #19 (kakṣyā key); lesser #18/#20/#21/#23/#26 | **accepted** | Oracles O-GR-PLATEAU (#24, also protocol v2.0 §B peak-diversity), O-P6-TARA (#5), O-BP-4 (#19); #18/#20/#21/#23/#26 each get an oracle or an explicit guarded-by-construction note in the v1.1 §11.2 index (#20/#21/#22/#23/#26 per Codex coverage table below) |
| F4 | §9 stale: B3.3 landed activation [D] (three modes); D-RQ3 recount complete | **accepted with amendment** | Specs v1.1 §9.2: activation admitted [D] as **three separate modes kept distinct** (sahameśa-daśā PG95:C1; varṣeśa contact PG147/PG160; munthā/muntheśa contact PG132/PG160) — NO synthesised universal conjunction (Codex S-06); Mudda labelling [U] retained; P2 gains the node Moon-relative line [D] with N-14 restated |
| F5 | 10,592 not 10,587; "22 oracles" vs actual 25; v3.0 §6.1 Moon count verified | **accepted** | Arithmetic fixed in protocol v2.0 (H = 10,592 full horizon; masked horizon 10,334 — both derived, printed); oracle count stated truthfully in v1.1 |
| F6 | Schema ambiguities: relation enum mixing; unscaled evidence fields; object_role vs relation overlap | **accepted** | Specs v1.1 §1.1: `relation` split into `transit_relation` vs `natal_relation` usage table; evidence fields declared rank-only, scale deferred to calibration (L5); `object_role` declared authoritative for role, `relation` for physical relation |
| F7 | O-PP-2 tests non-constancy, not correctness | **accepted** | O-PP-2 replaced: known related period (Mercury/Ketu, 7th-adjacent) vs known unrelated period, boundary cases at AD transitions; non-constancy retained only as a secondary smoke check, labelled as such |
| Q-M1 | No re-run of '3.0' needed; remediation adequate | **overridden** | Native instruction 2026-09-29 item 7 (and Codex Q-M1): re-run under protocol v2.0 from a pinned extract; v1_0 kept as disclosed history |
| Q-M2 | T-rank construction sound; floor miscounted (26 not 23 ⇒ 14 not 12) | **accepted with amendment** | Protocol v2.0: floor = `floor(M/2)+1` computed from the **audited registry cohort**, not a hard-coded number; under the v2.0 registry M is recomputed and printed (see EVENT_REGISTRY_v2_0.md) |
| Q-M3 | T-FP honest but is aggregate-density applied per class; alternative per-class bar acceptable | **accepted with amendment** | Protocol v2.0 adopts **per-class budgets** `B_c = min(1, 3·n_c·90/H_c)` (Codex Q-M3 alternative 2; native's "pick one and show the arithmetic"); arithmetic printed per class |
| Q-M4 | Single capped-miss median sound; 182 d fine | **accepted with amendment** | Cap applied to **all** timing errors (Codex M-06), not misses only; misses reported separately alongside; median convention for even cohorts stated |
| Q-M5 | Oracles failable, arithmetic verified; load-bearing gaps as F1/F2/F3 | **accepted** | As F1–F3; per-oracle repairs also per Codex Q-M5 table |

## B. Codex (Astra) findings

### B.1 Structural / doctrine (S-01…S-08)

| # | Finding (abbreviated) | Disposition | Where resolved |
|---|---|---|---|
| S-01 | Evaluator/relationship schemas not build-complete (no path_id, versions, null states, aggregation) | **accepted** | Specs v1.1 §1–§2 rewritten as typed contracts: `relationship_record` gains `path_id`, `rule_version`, `contact_id` FK, `generation`; `rule_path`, `predicate`, `factor`, `eval_window` schemas with keys, FKs, null states; cross-path aggregation rule (union admits; score = per-path product aggregated by max, then ranked; conflicts keep both evidence fields) |
| S-02 | Physical identity/lineage unreconciled (alias hashing, rounded t_exact, truncated contacts, invalidation) | **accepted** | Specs v1.1 §6: canonical physical-object identity = (body, relation, target canonical id, method_version) with rounded-value hashing forbidden (hash the solved value at full precision + method_version); truncated-contact identity includes `coverage.truncated`; invalidation keyed on whether required geometry changes (re-solve) vs interpretation (re-score), dependency-driven |
| S-03 | O-RP-5 reverses adverse evidence; prose vs JSON O-RP-5 are two different tests; mixed ≠ uncertain; P3 "house and its lord" ambiguous | **accepted** | Specs v1.1: O-RP-5 = one test, same in prose and JSON — Saturn 8th-from-Moon residence is **evidence FOR adverse classes** (P2 adverse-residence scoped to adverse classes per D-RQ5) and does not attach to gain classes; occurrence-conflict vs outcome-valence separated (§3: `evidence_for`/`evidence_against` both high ⇒ occurrence contested; `outcome_valence_for_native` derives from class polarity only — "mixed" is a valence verdict, never an uncertainty state); P3 rewritten as explicit Boolean operators with a per-class truth table (§2 P3 + truth table) |
| S-04 | Source status / admission / scoring permission conflated | **accepted** | Specs v1.1 §0/§1: provenance (`verse_cited` / `uncited_extension`) separated from operator role (`scored` / `testimony`); every D-PADMIT element (node-dispositor, māraka, **all Moon-channel P6 practices**, mūrti) is testimony-only until its named promotion gate (B5.4 ablation evidence); P9 stays behind D-T2; a source read never promotes an operator |
| S-05 | AV semantics: unruled "sign mean" comparator; contradictory fallback; P5d operand conventions; no #26 fixture | **accepted** | Specs v1.1 §8/§2-P5: sign-mean comparator **removed** (D-RQ1 rules only: more-marks favourable / fewer adverse / known-zero adverse / unresolved = unqualified — no population-mean test); P5a–e specified independently, each with own operands and missing-data states (missing donor data disables P5c only); P5d gets remainder convention (mod 27, remainder 0 ⇒ 27th nakṣatra) and operand provenance; O-BP-5 fixture: measured SAV vs `min_sav_score` (#26 proxy regression) |
| S-06 | Corpus-read register overstates what it settles (textbook example ≠ chart operands; synthesised universal saham rule; OCR uncertainty; unverified annotations) | **accepted** | Specs v1.1: chart-specific AV operands marked **unresolved** until a pinned L1 extract supplies them (names the precondition; G-10); saham activation = three separate modes (no universal rule); OCR uncertainty recorded per-clause (Aṣṭottarī v.23 pakṣa wording; MC cycle/thirds "[?]" at PG67:C1); measurement guard in protocol v2.0 §7: event annotations enter scoring only via LEL_CHART_STATE_RECONCILED, unverified annotations rejected |
| S-07 | Oracle coverage/falsifiability: 25 ≠ 35 named; O-AO-1 impossible join; O-PP-2 proxy; O-CF-N5 bad fixture | **accepted** | Oracles v1.1: one authoritative inventory with the true count; O-AO-1 rewritten (year-qualified join returns the match; kind-only join flagged as the defect it tests); O-PP-2 replaced (see F7); O-CF-N5 gets real fixtures (two eligible peaks < 90 d apart must survive production); O-CF-N6 gets a non-empty control class; every oracle carries a literal fixture plus a mutation that must fail it |
| S-08 | Arithmetic: 3.64° = 3°38′24″ (not 3°39′); Ketu–lagna 0°33′36″; E1 zero-width sum 136,883; natal Venus 259.19 (259.1882); hash suffixes | **accepted** | Fixed in specs v1.1 §11.3, oracles v1.1 constants (Venus 259.19), protocol v2.0 (H figures), and the review-packet hashes (full sha256, this file §D). E1 conclusion (98.6 %) unchanged. Rounding rule pinned: degrees→DMS truncation to the second; decimal-degree display rounds half-up at 2 dp |

### B.2 Measurement (M-01…M-06)

| # | Finding (abbreviated) | Disposition | Where resolved |
|---|---|---|---|
| M-01 | Event population loses observation meaning (CURRENT.01 a status not an onset; 2026-03-20 a closure; 2026-04-08 a clearance; MBA enrolment omitted; grandfather June-or-July; inconsistent quarry mapping) | **accepted** — each claim verified at source this session (LEL:1558–1584 status-only; LEL:1500–1508 closure; LEL:1529–1537 clearance; LEL:674–682 enrolment; LEL:549–553 "June or July"; LEL:22 CURRENT.01 not a point event) | measurement/EVENT_REGISTRY_v2_0.md: row-level registry — observation type (onset/status/interval), date + uncertainty, class mapping with printed reasons, inclusion + exclusion reasons; CURRENT.01 excluded from dated scoring; 2026-03-20 remapped (see registry, disclosed as a judgment call); 2026-04-08 excluded (no engine class; operation event is post-mask); enrolment included; grandfather = 2-month uncertainty interval |
| M-02 | Horizon/counts/floor wrong (26 not 23 timing-usable; hits 21/36 not 22; H = 10,592; 258 unobserved days; 1995 event inside a 1998-start horizon) | **accepted** | Protocol v2.0: observation mask ends 2026-04-17 (masked horizon 10,334 d, printed derivation); events before 1998-01-01 excluded with reason; every numerator/denominator recomputed in the v2.0 re-run from the registry, not copied from v1_0 |
| M-03 | Metrics not reproducible (resolution-tier mismatch hit-vs-burden; "coverage" conflation; class universe from output rows; no materialised random controls; timezone unstated; ties/missing ranks undefined) | **accepted** | Protocol v2.0 §2–§5: fixed class universe (the 27 engine classes, declared ex ante); prediction surface = one declared tier policy used identically for hits and burden; timezone = IST with the 18:30-UTC storage convention stated; ties, misses, uncertain intervals defined; 20 random controls per event materialised from seed 482012 in the re-run appendix; coverage read from manifests, never inferred from output sparsity |
| M-04 | T-rank selective-validity risk (misses vanish from the median; N inflatable by subdivision) | **accepted** | Protocol v2.0: eligible misses stay in the rank endpoint at worst-rank convention (percentile 100); candidate identity/dedup = maximal windows (merge overlapping same-class windows before counting N); ties = average rank, disclosed as not measuring chronological discrimination; floor from the audited cohort (Q-M2) |
| M-05 | T-FP derivation changes denominator mid-argument; adverse-class membership inconsistent | **accepted** | Protocol v2.0: adverse-class membership frozen in the registry (bereavement, career_setback, chronic_onset, financial_deception, illness_acute, parental_event, separation, surgery, major_loss); per-class budgets `min(1, 3·n_c·90/H_c)` with the arithmetic printed; all-observed-time burden kept distinct from negative-year burden and from any statistical FP rate |
| M-06 | 182-day miss cap asymmetric (hits at 686/998 d exceed it) | **accepted** | All timing errors capped at 182 d; uncapped hit errors and miss count reported separately; 182 d labelled a policy convention, not evidence-derived |

### B.3 Codex explicit measurement answers (Q-M1…Q-M5)

| # | Answer | Disposition |
|---|---|---|
| Q-M1 | Preserve historical pass; re-run under corrected protocol from a pinned extract; recompute candidates under the same protocol; blindness not restored, amendments stay disclosed | **accepted** — exactly what B3.6 does (extract + BASELINE_3_0_v2_0.md); '4.1'/'5.0' scoring waits for the native's protocol-review close |
| Q-M2 | Restore T-rank; floor(M/2)+1 only if "majority of audited cohort" is the policy; recompute denominator after M-01 | **accepted** — policy stated as majority-of-audited-cohort; M recomputed from the v2.0 registry |
| Q-M3 | Pick pooled-union budget OR per-class `min(1, 3·n_c·90/H_c)`; show arithmetic; mask unobserved days | **accepted** — per-class budgets chosen (pooled union cannot distinguish a class that is always-on from one that is tight while others carry the load); arithmetic printed in protocol v2.0 §4; unobserved days masked out of H |
| Q-M4 | Single median conditionally sound; cap hits and misses consistently; even-cohort median convention | **accepted** — v2.0 §4 T-time: median over capped errors (lower of the two middle values averaged, standard convention, stated) |
| Q-M5 | JSON does not establish falsifying tests; per-oracle corrections table | **accepted** — every row of the Q-M5 per-oracle table implemented in oracles v1.1 (see the JSON's `rework_note` per oracle) |

### B.4 Codex defect-coverage rows that demanded new guards

| Defect | v1.0 disposition per Codex | B3.6 disposition |
|---|---|---|
| #1 promise saturation | Lost | **accepted** — specs v1.1 §2 invariant: promise consumes strength AND condition; oracle O-RP-6 (a constant-presence implementation must fail) |
| #5 tārā key | Lost | **accepted** — oracle O-P6-TARA: tārā term present with the declared key on a P6 evaluation; key-normalisation fixture |
| #19 kakṣyā key | Distorted | **accepted** — oracle O-BP-4: donor-key resolution per CORPUS_READS §8 (PG301); sign-level fallback is labelled coarser qualification, never donor evaluation |
| #20 strength/dignity/maitrī | Lost | **accepted** — specs v1.1 §2 P1 factor list names each input with a declared effect; oracle O-RP-7 (dignity operand flipped ⇒ P1 qualifier flips) |
| #21 ontology fields / Cartesian agents | Lost | **accepted** — oracle O-RP-8: `transit_triggers`/qualified restrictions control enumeration; a Cartesian all-pairs run must fail |
| #22 yoga→event relation | Lost | **accepted** — oracle O-RR-5: a cited yoga→event relation resolves with cancellation and strength consumed |
| #23 "afflicted" as label | Lost | **accepted** — specs v1.1 §1: affliction is an evaluable predicate (named afflicter set, relation, orb), not a label; oracle O-RR-6 |
| #24 plateau | Partial | **accepted** — spec oracle O-GR-PLATEAU (era/month/day rows trace to a path operating at that grain) + protocol §B peak-diversity |
| #26 mūrti/w21 proxy | Lost in part | **accepted** — mūrti stays testimony (D-RQ4); `min_sav_score`-as-SAV proxy guarded by O-BP-5 (measured SAV fixture) |
| N9 unverified LEL annotations | Lost as completion guard | **accepted** — protocol v2.0 §7 annotation guard + registry carries verification state per row |

## C. Cross-review agreements and the one disagreement

Both reviewers independently: confirmed the same packet hashes; recomputed the same arithmetic
(10,592 d; 3°38′24″; 3°57′; 26 timing-usable; floor 14); found the aspect-direction guard the
highest-value omission; found the JSON inventory short of the spec index.

**The one substantive disagreement** — re-run of '3.0': Kimi Q-M1 ("ceremony; do not re-run")
vs Codex Q-M1 ("recompute under the corrected protocol from a pinned extract"). Resolved by the
native's instruction #7 (2026-09-29): **re-run**, with the earlier run kept as disclosed
history. Recorded as OVERRIDDEN (Kimi) / ACCEPTED (Codex), not adjudicated on merit.

## D. Full hashes of the review surface (sha256, recomputed 2026-09-29 on campaign/pravaha)

| Artifact | SHA-256 |
|---|---|
| design/GOCHARA_DESIGN_SPECS_v1_0.md | c87919dbe06fc6828ee719805143a319898b6ebd4c0ae502d67deb14a5debea0 |
| design/GOCHARA_TEST_ORACLES_v1_0.json | 4bd029feddf1ebc19b1f951ec5dc341eca80222666a981ce81b471c31dd1c95b |
| design/GOCHARA_PLAN_V3_AMENDMENT_v1_0.md | bb5bc981419ff9b33de4490b90a1849da52c3e60d78975b4b50f5b4fd804f9d9 |
| design/L3_FAMILY_COORDINATION_v1_0.md | 2476f2ccb7fcd6ebbaa4e472ffe8e17726d3fb0a62dc8e603fe2931d6dd926aa |
| design/CORPUS_READS_v1_0.md | 818debe3a65487dd60618a543ddebff5a3ddd14927908146c9b6e3b6112128b5 |
| measurement/EVALUATION_PROTOCOL_v1_0.md | c7c5a8370443c8d24b73336b3693ed7f63f793b838478e185f620724b0efbb0f |
| measurement/EVALUATION_PROTOCOL_v1_1.md | e093010dff71b15b67629d6796227843632a894d73d7ab58b3dba7cef821bd2f |
| measurement/EVALUATION_PROTOCOL_v1_2-DRAFT.md | 8ab737edf0cdf931509171da79631bd3d22bce059fa1eb1e96fc98139ae50f16 |
| measurement/BASELINE_3_0_v1_0.md | 8562c6c885d67a102723bc7949154e2ffb03973562e4a5f91ed7cee9f35d1a75 |
| sealed/FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0.md | 5bd6c51e8901399ef05090f4b3e9933f69735773effff945cfce78e45e182392 |
| sealed/FABLE_REVIEW_EVIDENCE_APPENDIX_v1_0.md | 05ce2f0d9ecdc4b7a3f166c1bdb9a364760f8bc09ed0407f667f91fcc204ff20 |
| NATIVE_DECISION_PACKET_v1_0.md | 89263ffdc09974bf7b8bf22bc5ebd17a7c2043d5a12eb17cb1493f359e4f0b0c |

(Kimi's six and Codex's eight recomputed hashes agree where they overlap; the table above is the
union, recomputed here. Full hashes replace the packet's abbreviated suffixes per S-08.)

## E. What B3.6 does NOT do

- Does not set `status: FROZEN` on the reworked specs — the native decides whether v1.1 goes
  back to review before D-SPECS.
- Does not score '4.1' or anything else — no scoring until the native reports the protocol
  review closed.
- Does not dispatch any reviewer.
- Does not reopen any native ruling; every correction above implements the rulings as given.
