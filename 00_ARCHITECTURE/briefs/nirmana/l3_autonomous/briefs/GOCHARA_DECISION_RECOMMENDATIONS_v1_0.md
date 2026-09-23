---
artifact: GOCHARA_DECISION_RECOMMENDATIONS
version: "1.0"
status: REVIEWED_AND_RECONCILED
superseded_by: "GOCHARA_RULING_SHEET_v2_0.md (the reconciled rulings for the native's authorization); review KIMI_K3_REVIEW_GOCHARA_DECISIONS_v1_0.md; dispositions KIMI_RECONCILIATION_GOCHARA_DECISIONS_v1_0.md. Retained as the text the reviewer read; three of its recommendations (N-15 locus, M-1 attribution, M-7 source) were corrected there."
date: 2026-09-23
scope: "Every decision left pending on the native after the WP0–WP7 campaign closed (FINAL_REPORT_v1_0.md, commit df8b05576; reconciliation commits 59bebe7dc / 28fd59245 / c0e7b1b13). One recommendation per item, with the evidence it rests on, its cost, its falsifier, and what it does not decide."
basis: "GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md (NATIVE_RATIFIED_PLAN) · GOCHARA_RULING_SHEET_v1_0.md (D-1..D-3, R1–R10, N-1..N-14 ruled; M-1..M-8 ruled in direction) · WP0_FINDINGS.md · WP1_CONTRACTS.md · WP3b_CLASSIFICATION.md · WP4_DECOMPOSED_COMPARISON_v1_0.md · WP6_LEDGER.md · wp7_packets/ · ESCALATIONS.md (E-001..E-006)"
evidence_labels: "[X] executed in this campaign · [L] live read of the served corpus table classical_text_chunks, 2026-09-23 (counts by predicate, never a directory or the search tool — F-32) · [S] source at HEAD c0e7b1b13 · [R] repository record · [D] doctrine (text named) · [P] practice · [J] judgment · [U] unverified"
authority: "Recommendations only. The native rules; nothing here executes anything. Where a recommendation would change served λ, it is marked SCORING-CHANGE and tied to the WP10 candidate generation, never a patch over live rows."
---

# Gochara — the pending decisions, with recommendations

## §0 Two corrections to the residual plan I gave the native

1. **N-14 is not pending.** `GOCHARA_RULING_SHEET_v1_0.md` §1 already rules it ("extend *no graha-dṛṣṭi for Rāhu/Ketu* to this family", three conditions). What remains is **execution at WP10** (ESCALATIONS E-005). I listed it under "your decisions" in the residual plan; that was wrong. It appears below only as an execution dependency.
2. **The Sade-Sati corpus count was understated and its conclusion is now stronger.** I reported "one row in the whole corpus". A broader predicate (all spellings plus "Saturn … 12th … Moon") returns 8 rows across 4 texts `[L]`; I read the 5 non-nāḍī rows (`brihat_jataka` PG178/PG328, `jataka_parijata` PG215/PG232, `bphs` PG845) and **every one is an unrelated natal-placement passage or an aṣṭakavarga chapter fragment** — none states the Saturn-around-the-Moon transit doctrine. So the admitted corpus holds **zero** primary-text support for Sade-Sati as a transit rule; the only matches are nāḍī rows. See N-15.

## §1 What is pending, and in what order to rule it

| Order | Item | Class | One-line recommendation |
|---|---|---|---|
| 1 | **M-1** activity decay shape + orb values | method parameter | **linear in separation, the engine's own existing decay law, with the ±5-day time box removed**; WP1 §7 orbs as the WP8 candidate; numbers ratified on the marriage-2013 + ordinary-quarter comparison |
| 2 | **M-8** vedha exceptions + vipareeta semantics | method (ruled to implement; semantics open) | exceptions → **no row**; vipareeta → row kept, `cancelled=true`, no suppression; retrograde-malefic vedha → typed qualifier, weight on evidence |
| 3 | **M-2** dwell / retrograde | method | **split**: dwell weight **not admitted**; retrograde-state **qualifier admitted** as typed testimony (Phaladīpikā, verified) |
| 4 | **M-6** new target classes | method | **Gulika/Māndi first** (primary source found in Phaladīpikā XVII — reverses my earlier demotion), scoped to the classes the text names; bhāva-ārūḍhas second, `uncited_extension=true`; special lagnas / Prāṇapada / nakṣatra-pādas deferred (0 rows) |
| 5 | **N-16** *(new)* mechanism wiring truth is stale | honesty | make `MECHANISM_ENGINE_WIRED` derived from `engine.py`, or a test that fails on disagreement — **before** M-4's audit runs |
| 6 | **M-4** mechanism admission audit | process (ruled); order open | audit order and interim admissions per §2.5's matrix |
| 7 | **M-7** bindu-qualified kakṣyā | method, gated | commission **G-10** (L1 per-contributor BAV) and a **re-OCR of BPHS ch.66** (G-9 sibling); interim = sign-level BAV qualification, declared coarser; grid stays `uncited_extension=true` |
| 8 | **M-3** Moon channel | method | separate channel; **Moon never enters the century λ**; Moon-scale classes only; tārā-bala is the Moon's classical entry (already live — see N-16) |
| 9 | **N-15** *(new)* Sade-Sati factor | SCORING-CHANGE | downgrade from λ factor to **typed testimony** (`corpus_verifiable=false`) in the WP10 candidate generation; commission a primary-source ingestion |
| 10 | **N-17** *(new)* H-5 producer side | pre-approved fix, unblocked | implement cap-free admission now (A-class; `resolution_hierarchy.py` is in `may_touch`; P-1 v1.1 §3.6 defines the serve-time trim); served data untouched until WP10 |
| 11 | **N-18** *(new)* publish the campaign branch | delivery | push `l3/gochara-autonomous-wp0-7` (13 commits, unpushed) and open the PR to `main`; merge is code-landing only — no build runs under the standing order |
| 12 | **N-19** *(new)* E-001 artifacts | delivery | land `KALA_COST_PROFILE_v1_0.md` + `KALA_BASELINE_v1_0.md` on `main` from `l3/kala-setup-phase01` (`bb7857b07`, `de2a7f269`) |
| 13 | **N-20** *(new)* E-004 admin scripts on `_v2` | scope | **no new guard**; add to the reader inventory; re-check at N-11 (they touch `'2.0'`, which N-11 deletes) |
| 14 | **A-1** WP9 authorization + Moorti method | authorization + method | authorize WP9's engineering half now (A-class); rule Moorti **at the true ingress instant** with the day-grade error rate reported |
| 15 | **A-2** WP10 tranche 1 (runbook steps 0–5) | authorization (P-class) | authorize as a tranche: Clear fix → grant → restore drill → guard + N-6a → schema 1075/1076 → registry re-pin + C-1 |
| 16 | **A-3** WP10 tranche 2 (steps 6–10) | authorization (P-class) | gated on tranche-1 evidence **and** P-1 + C-1 landed; the first `'4.0'` candidate carries N-14, N-15, N-17 together |
| 17 | **O-1 / O-2 / O-3** owners | assignment | name an implementation owner per packet, an independent reviewer who is not the author, and a fresh session for Kṣetra rulings 7/8/9 |
| 18 | **G-6..G-10** commissions | routing | L0: G-6 receipt, G-8 strike, G-9 re-cite at page grain (+ the ch.66 re-OCR); L1: G-10; Saṅgam: G-7 (likely closed by their M-1) |

## §2 Method calls (WP8) — recommendation, evidence, cost, falsifier, not-decided

### 2.1 M-1 — activity decay shape and orb values

**Ruled direction (sheet §2):** orb-scaled within the declared orb, replacing the legacy ±5-day box; BPHS ch.26 ślokas 6–8 (dṛṣṭi-koṇa) as the warrant.

**Evidence, new since the ruling.**
- The warrant is **corpus-verifiable in the served table**: 7 `bphs` rows match `drishti kona | aspectual angle/value` `[L]` (it was verified in the OCR file earlier; this closes the loop against the table the instrument actually serves).
- **The engine already carries a linear decay law.** `legacy_semantics.py:337` reproduces `engine.py:222`: `p_i = 1 − min(orb_degrees / ACTIVITY_MAX_ORB_DEG, 1)` `[S]`. What makes today's served activity a step is not the decay law but the **±5-day time box** around `t_exact` that feeds every sentence inside the box as an exact contact (`orb_legacy_box`, WP1 §7).
- **WP4 measured the two shapes on one anchor** `[X]`: at `t_exact + 4 d` on the Saturn leg (speed 0.017454°/d → separation 0.0698°), legacy λ = 0.80000 (box), kernel λ = 0.74415. Since the anchor λ is 0.80 (promise × permission), the kernel's activity there is 0.9302 = 1 − 0.0698/1.0 — i.e. **linear decay with the WP1 `orb_conj_slow` = 1.0°** reproduces the measured value to four decimals. The shape in play is already linear; the delta is entirely the removal of the box.
- Dṛṣṭi-koṇa in the text is **piecewise-linear in separation** (the śloka computes the aspect value by linear slabs of the degree difference), which is a doctrinal reason to prefer linear over cosine or any curvature the text does not state `[D]`.

**Recommendation.** Rule the **shape** now: linear in angular separation, `activity_i = 1 − |Δ| / orb_max_deg`, zero outside the orb, **no time box**. Rule the **orb values** only on WP8 evidence: adopt WP1 §7 (1.0° slow conjunction/dṛṣṭi, 3.0° Moon, 0.5° slow return) as the *candidate*, run the two named walkthroughs (marriage 2013; ordinary quarter 2027-03→05) box-vs-linear at 0.5°/1.0°/2.0°, and ratify the value that best separates the 13 envelope-only classes into real windows without inflating the count of active days beyond the legacy count (that is the discrimination test; a value that only makes more windows is not better).
**Cost:** one projection change; the WP8 comparison PR. **Falsifier:** the walkthroughs show linear decay does not improve discrimination over the box at any candidate orb. **Not decided:** per-relation orb values; Moon's orb (M-3 first).

### 2.2 M-8 — vedha exceptions and vipareeta vedha: row semantics

**Ruled:** implement, verse-cited (sheet §2). Open: what a row *is* under each rule.

**Evidence** `[L]`: Phaladīpikā Adh. XXVI — Sun's pairs with the Saturn exception at `PG322:C1`; Mercury's with the Moon exception at `PG323:C1`; retrograde intensification at `PG348:C1` (*"Malefics when retrograde will cause intense evil if they are in Vedha position, while benefics will do immense good"*) and `PG350:C1` (*"death if the motion be retrograde; if direct, the sickness will soon subside"*); vipareeta vedha in the served `bphs` (1 row, the ch.31 translator note; the OCR file at `bphs_vol1:24414-24441`).

**Recommendation.**
- **Exception (Sun–Saturn, Moon–Mercury; Saturn in the 9th against Sun in the 3rd):** the writer emits **no vedha row at all** — the doctrine says the obstruction does not arise, so there is nothing to record; the coverage manifest records the pair as `searched, exception_applied` so the absence is a searched negative, not silence.
- **Vipareeta (a second graha joins the transiting graha):** the vedha row is **kept**, with `cancelled=true`, `cancelled_by=<graha>`, `suppression_factor=1.0`, and the cancellation instant. Keeping the row preserves testimony (the obstruction existed and was lifted) and lets Kṣetra/Saṅgam see the cancellation rather than an unexplained gap.
- **Retrograde malefic in vedha position:** a typed qualifier `intensity_qualifier='retrograde_malefic'` (F04 `[D]`) on the row; **no numeric weight now** — that weight is exactly what M-2's retrograde half puts to WP8.
**Cost:** two fields + one coverage state; G-O packet. **Falsifier:** a corpus passage that says a cancelled vedha still obstructs partially — none found. **Not decided:** the weight of a retrograde-malefic vedha.

### 2.3 M-2 — dwell weighting: split, and rule each half

**Ruled:** deferred, lean skeptical. **Evidence changes the shape of the question** `[L]`: no admitted text speaks of *dwell* (duration, slowness) as a weight; but Phaladīpikā speaks of **retrograde state** three times in transit context (PG348, PG350, and Adh. XIX śl.37 at `PG250:C1`: the bhukti lord's transit *"or be retrograde — the effects will then be good"*), so retrograde is doctrine, dwell is not.

**Recommendation.** (a) **Dwell weight: not admitted**; `dwell_days` stays a geometry field. (b) **Retrograde-state qualifier: admitted as typed testimony** on every episode (`branch ∈ {direct, retrograde, station}` already exists) and on vedha rows (2.2). (c) Whether the qualifier carries a *weight* in λ is a WP8 ablation on held-out chronology, not a ruling now — the text says "intense evil" and "good", not a number.
**Cost:** none for (a)/(b) — fields exist. **Falsifier for (a):** an admitted text stating slowness or duration as a strength factor. **Not decided:** the retrograde weight.

### 2.4 M-6 — new target classes: order and citations

**Ruled:** bhāva-ārūḍhas first, Gulika/Māndi after its rule is re-found, others deferred — an order I set after discovering the Gulika rule I had cited lived in a KP file not in the corpus.

**Evidence, new** `[L]`: **Phaladīpikā Adhyāya XVII is a chapter of death-timing transit rules built on Māndi/Gulika-derived points**: `PG220:C1` śl.26 — *"Ascertain how far Mandi is removed from the lord of the 8th house. When Saturn in his transit arrives at a Rasi so far removed from Mandi, death may happen"*; `PG214:C1` śl.6–8 and `PG217:C1` śl.14 — subtract Yamakaṇṭaka's figures, transit of Jupiter/Saturn over the resulting rāśi/navāṃśa; `PG219:C1` śl.22; `PG218:C1` śl.28. Sarvārtha Cintāmaṇi `PG1:C217` names the navāṃśa lords of Māndi/Gulika among the māraka planets when Saturn transits the 8th. **Special lagnas + transit: 0 rows; Prāṇapada + transit: 0 rows; ārūḍha + transit: 1 row, nāḍī only** `[L]`.

**Recommendation.** Reverse the order I gave: **Gulika/Māndi first**, verse-cited to Phaladīpikā XVII, and **scoped to the classes the text names** — death/māraka, acute illness, and their derived points (distance-from-Māndi, Yamakaṇṭaka-difference points), not as a general target for every class. **Bhāva-ārūḍhas second**, as interval targets, `uncited_extension=true` (Jaimini rāśi logic is structural; no transit-to-ārūḍha passage in an admitted text). **Special lagnas, Prāṇapada, nakṣatra-pāda points: deferred** — 0 rows by count for the first two; the third not counted here and should be before any admission.
**Cost:** Gulika/Māndi needs the derived-point resolution rules (distance-from-Māndi, Yamakaṇṭaka arithmetic) written into the WP1 target contract as new rows — small, deterministic, citable. **Falsifier:** none for admission; the *classes* are falsified if the text is read as general rather than māraka-scoped. **Not decided:** weights.

### 2.5 M-4 — mechanism admission audit: order and interim admissions

**Ruled:** operand audit first, two-step admission, W21 not first, bindu weighting studied in the same audit.

**Evidence** `[S][L]`: the register lists 10 "admitted" mechanisms demoted in MR-19 to *defined + cited + coded, not engine-wired*, with `w44_weight_fitting.py:124-138` `MECHANISM_ENGINE_WIRED` (all `False`) declared the "authoritative, LIVE, machine-checked source" of wiring truth. **That dict is stale:** `engine.py:186` `_W23_TARA_BALA_ENABLED = True`, `:675-680` computes `tara_modifier`, `:700` multiplies it into `raw_lambda`; `w30` (`:175`, `:696`) is not in the dict at all. WP3b P-2 already recorded w23's docstring still saying "NOT wired" while it is live. **A wiring-truth source that disagrees with the code it describes is a §N.8 null signal** — N-16.

| mechanism | operand available in L1/L0? | corpus-verifiable? `[L]` | recommendation |
|---|---|---|---|
| w26 real eclipses | yes (L0 instants; H-4 live) | eclipse doctrine present (not re-counted here) | **keep** |
| w23 tārā-bala | yes (natal Moon nakṣatra) | Muhūrta Cintāmaṇi in corpus (274 chunks; tārā not re-counted) | **validate, then keep** — it is already live; the audit's first act is N-16 |
| w21 AV gating | **sign-level BAV yes** (`ashtakavarga_bindu_sign` 96 rows); per-contributor **no** (G-10) | aṣṭakavarga chapters in `bphs` | **admit at sign level**, declared coarser; per-kakṣyā waits for G-10 (M-7) |
| w27a Tājaka year lord | Tājaka text present (`tajaka_neelakanthi` 290 chunks); my "year lord/muntha" predicate matched Sārāvalī 3, Bṛhat Saṃhitā 1, Yavana 1 and **0 in the Tājaka text itself** — predicate or translation issue, `[U]` | `[U]` | **audit its operand and citation before admission**; not first |
| w22 mūrti nirṇaya | data wired (F-MOORTI-2) | thin: 6 rows / 3 texts, none a transit-quality rule | **qualifier, not weight**, `corpus_verifiable=false` |
| w24 Sade-Sati | data yes (4,492 facts) | **none** (N-15) | **downgrade to testimony** (N-15) |
| w25 Kota | data yes (585 rows) | **0 rows corpus-wide** | **stays proposed-use** (N-8) |
| w27 annual stack | — | gated on G-2 | deferred |
| w27b Tithi praveśa | edge retired (N-8) | not counted | deferred |
| w27c Sudarśana | — | not counted | deferred |
| w30 nodal dṛṣṭi | — | citation refuted (F-29) | **retired** (N-14, WP10) |

**Recommendation.** Audit order: N-16 → w23 (validate the live one) → w21 sign-level → w26 (confirm) → w22/w24 (re-type as qualifiers) → w27a (operand + citation) → the rest deferred. The bindu weighting (M-7) is studied inside the w21 step. **Cost:** one audit PR per row. **Falsifier:** an ablation on a non-empty corpus showing a "qualifier" mechanism discriminates as a weight — then it is promoted, on that evidence.

### 2.6 M-7 — bindu-qualified kakṣyā

**Ruled in principle**, gated on G-10. **Evidence, new** `[L]`: searching every admitted text for kakṣyā in the aṣṭakavarga sense (`kaksha|kakshya|kaksya|eighth part of a sign|3¾|3°45`, with `ashtakavarga|bindu|rekha|transit` context) returns **nāḍī 6 rows and 1 Uttara Kālāmṛta row**; the 14 earlier "kakṣyā" hits in Sārāvalī / Uttara Kālāmṛta / Jaimini are **"Kakṣyā Hrāsa"** — a Jaimini longevity reduction, a different doctrine. **No admitted text carries the aṣṭakavarga kakṣyā division or its lord order**; BPHS ch.66 exists in the corpus but its kakṣyā ślokas are missing from the OCR (F-27). The served order (Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon, Lagna) is verified as *software fact* at two code sites (WP1 §8) and nowhere as text.

**Recommendation.** (a) Commission **G-10** (L1 per-contributor BAV matrix) — the mechanism cannot be classical without it. (b) Commission a **re-OCR of BPHS ch.66's kakṣyā pages** as a G-9 sibling: the doctrine's canonical home is that chapter; the corpus has the chapter but not the passage, which is an ingestion defect, not a doctrinal absence. (c) **Interim**: sign-level BAV qualification (w21) declared as the coarser qualification; kakṣyā rows keep `uncited_extension=true`, `corpus_verifiable=false`. (d) WP8 hypothesis to test, **not** a ruling: contribution scales with the transiting graha's bindu count in the sign (0 → `unqualified`, no activity; 1–3 damp; 4 neutral; ≥5 amplify) — the same three-band shape w21 already encodes (`<28 / 28 / >28` on SAV), so the audit compares one convention, not two.
**Cost:** L1 work (G-10); an OCR task. **Falsifier:** the re-OCR yields a passage whose lord order differs from the served one — then the served order is a defect, not a convention.

### 2.7 M-3 — the Moon's participation

**Ruled direction:** separate testimony channel; ADJ-14 stands. **Evidence** `[L]`: no admitted text scores *daily Moon transits* as a century-scale factor — the "Moon + transit + daily" predicate returns 2 Muhūrta Cintāmaṇi rows (both saṃskāra timing, unrelated) and 1 Sarvārtha Cintāmaṇi māraka row. The Moon's classical roles in gochara are as **reference** (janma rāśi/nakṣatra for every rule), as **tārā-bala** (w23, live), and in **muhūrta**.

**Recommendation.** (a) The century λ **excludes the Moon as a transiting body** entirely (no Moon activity term); (b) a **Moon channel** exists for Moon-scale classes (election, day quality, Moon-return-type questions) computed on demand with its own coverage record (§4.4), never persisted into the century ledger by default (R7); (c) the Moon's effect on slow-body windows enters **only** as tārā-bala and mūrti qualifiers at the instant — both already fields. **Cost:** a channel split in the projection; nothing new to compute. **Falsifier:** the walkthroughs discriminate better with Moon contacts blended into λ — I expect the opposite (F-09 saturation is partly Moon noise: 1,427 of the 3,319 served `drishti_contact` records are Moon).

### 2.8 M-5 — closed (restated for completeness)
Whole-sign primary; cusp only as a labeled KP-school variant. No parameter remains.

## §3 New decisions surfaced by the campaign (N-15 .. N-20)

**N-15 — Sade-Sati (SCORING-CHANGE).** The `quality_gates` factor consumes 4,492 Sade-Sati facts for this chart; the admitted corpus holds **no** primary-text statement of the doctrine (§0.2). Recommend: in the first `'4.0'` candidate, Sade-Sati moves from a λ factor to **typed testimony** (`epistemic_class` per F04, `corpus_verifiable=false`, phase carried as a qualifier); commission ingestion of a primary source (the doctrine is late and regional; which text carries it is `[U]` — the corpus owner should name one before it is re-admitted as a weight). Executed only in the candidate generation, never patched over live rows — same discipline as N-14. **Cost:** every stored λ changes (already true of N-14 in the same candidate). **Falsifier:** an admitted text stating the rule.

**N-16 — Wiring truth (honesty).** Make `MECHANISM_ENGINE_WIRED` a *derived* value (read the toggles and the λ product from `engine.py`) or add a test that fails when the dict and `engine.py` disagree. Today it says w23 is unwired while `engine.py:700` multiplies it. **Cost:** one test. **Falsifier:** n/a — it is a detector. **Executed 2026-09-23/24** (`l3/gochara-autonomous-wp0-7`): detector test `tests/l3/gochara/test_n16_mechanism_wiring.py` committed red-then-green; the dict and `mechanism_register.yaml` were corrected to the engine.py AST (w23/w30 wired, w28/w29 structural-unwired) with the test as the permanent guard; the citation-drift sweep re-pointed this document's `engine.py` refs to HEAD.

**N-17 — H-5 producer side.** Unblocked by P-1 v1.1 §3.6 (cap-free admission; serve-time trim with disclosed counts; never re-rank). Recommend implementing the cap removal in `resolution_hierarchy.py::retain_candidates_pooled` now (A-class, `may_touch`), with the kernel's `peaks.admit_peaks(max_rows=None)` semantics; nothing served changes until a build runs (WP10). **Falsifier:** a serving surface that cannot trim at serve time — P-1/P-2's job, and their packets say they can.

**N-18 — Publish the branch.** `l3/gochara-autonomous-wp0-7` is 13 commits ahead of `origin/main`, unpushed. Recommend push + PR. Merging lands code only: engine changes take effect in a *build*, and no build runs under the 2026-08-21 standing order; the resonance writer's corrections (R-1..R-6) likewise take effect only when resonance is rebuilt, which is sequenced at WP10 step 6. State that in the PR body.

**N-19 — E-001 artifacts.** Land `KALA_COST_PROFILE_v1_0.md` and `KALA_BASELINE_v1_0.md` on `main` from `l3/kala-setup-phase01`; until then the §10 Value row is CI-enforced `NOT_RUN`, which is honest but leaves the value claim unmade.

**N-20 — E-004 items 1–2.** No new staging guard for the W41–W45 admission scripts: they UPDATE `_v2` generation `'2.0'` and `g3_*`, neither of which the `'4.0'` publication touches; add them to the reader inventory and re-check when N-11 deletes `'2.0'`.

## §4 Authorizations (A-1 .. A-3) and owners (O-1 .. O-3)

**A-1 — WP9.** Authorize the engineering half now: Vedha and Moorti onto the kernel, coverage = requested horizon, the three-consumer stamps (`source_qualification`, `precision_regime`, `corpus_verifiable`), M-8's rows. **Rule the Moorti method:** grade at the **true ingress instant** (the reviewer affirmed it; the day-grade misclassification rate is reported alongside). Kota only after M-4's w25 row.

**A-2 — WP10 tranche 1 (runbook steps 0–5).** Authorize as one tranche with its evidence: Phase 1.1 Clear fix → Phase 1.2 grant → restore drill (38,287 rows content-checked) → (table, generation) guard + N-6a century `is_active=false` → migrations 1075/1076 applied and *verified* → registry re-pin + `EXPLICIT_CLEAR_OPS` (C-1). Nothing in this tranche builds or serves a row. Preconditions: N-18 merged; C-1 implemented by its owner.

**A-3 — WP10 tranche 2 (steps 6–10).** Gated on tranche-1 evidence and on P-1 landed. The first `'4.0'` candidate on the canonical chart carries **N-14 (w30 out), N-15 (Sade-Sati to testimony), N-17 (cap-free peaks), M-1's shape, M-8's rows** — one candidate, one regeneration, one manifest — then the four flip gates, flip, soak, second chart, N-11.

**O-1 implementation owner(s):** one per packet, each in its own worktree off `main`; the WP0–WP7 pattern (a Kimi session per packet at max effort with the escalate-don't-ask contract) worked and is recommended. **O-2 independent reviewer:** not the author of the packet; the K3 review + reconciliation loop is recommended per packet. **O-3 reviewer for Kṣetra rulings 7/8/9:** a fresh session with no stake, instructed to re-run the corpus counts.

## §5 What this document does not decide
WP10 execution timing; any retirement; any guard weakening; the numeric weights M-1/M-2/M-7 route to WP8; the corpus owner's choice of Sade-Sati source; the L0/L1 owners' scheduling of G-6..G-10.
