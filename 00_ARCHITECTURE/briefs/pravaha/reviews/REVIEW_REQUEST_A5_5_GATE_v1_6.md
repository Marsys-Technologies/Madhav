---
artifact: REVIEW_REQUEST_A5_5_GATE
version: "1.6"
author: "Stream B (Śāstra) — Exec B (Claude Sonnet)"
date: "2026-10-02"
reviewer: "Codex gpt-6-astra (max) — dispatched by the steward"
authority: "Review request only; authorizes nothing."
supersedes: "v1.5 (the packet round 6 is reading). THIS VERSION IS A DELTA REQUEST for round 7: §A lists what round 6 already has; §B lists only what is NEW; §C restates the standing pre-conditions and limits; §D is the judge-list for the delta."
---

# A5.5 gate — round-7 delta (2026-10-02)

## §A. Already in round 6 (v1.5) — do NOT re-review unless the delta below touches it

| Exhibit | Ref in v1.5 | Unchanged since? |
|---|---|---|
| Amendments draft **AM-1…AM-17**, AM-12 candidate, **PC-1…PC-4** | v0.10 | AM-1…AM-17 text unchanged (only the draft's version number and AM-18 were added — see §B) |
| **#2817** migration 1204 | head `b9d5d2718` | unchanged — accepted, HOLD |
| **#2867** migration 1206 v1.2 + Codex ACCEPT_WITH_AMENDMENTS | head `fc10a91fe` | unchanged |
| **#2884** migration 1220 (merged `dba48ec5c`) | merged | unchanged |
| **#2897** AM-13 registry (`activity_kernel@1.1.0`, `graduated_drishti@1.1.0`, P3/P4/P5 @1.1.0, kernel evaluator) | head `576907611` | unchanged — **round 6 is reading it now** |
| Merged code **#2869 / #2871 / #2881**; identity contract; window-sweep answer; **SI-mapping pre-registration**; **ND-ORB packet**; oracle map; prerequisite answer | v1.5 items 7–12 | unchanged |

## §B. NEW since v1.5

| # | Exhibit | Ref | What changed / what to judge |
|---|---|---|---|
| N1 | **AM-18 — RULED** (vedha source, value mapping, scopes) in the amendments draft | **v0.12**, `campaign/pravaha` (§AM-18; first a candidate in v0.11) | **Amends FROZEN text (§2.3 inv 3, §5.2 inv 1)**: "no soft factor zeroes an admitted window" → "…**excludes**…" so a cited nullification may drive a record's for-channel value to 0.0 while the window stays admitted. Source = derived from stored residence spans (36 cited L0 pairs; 6 L0-flagged UNSOURCED node rows unusable); active ⇒ 0.0, none ⇒ 1.0 (cited step, nothing graded); vipareeta not produced; nodes undecided ⇒ `unqualified`; scope `excluding_on_demand_moon_obstruction` on every 1.0 (Mercury primary exempt) |
| N2 | **`design/P2_VEDHA_ANSWER_v1_0.md`** (v1.1 adds the Moon sign-ingress evaluation) | `campaign/pravaha` | the cited basis for N1: Phaladīpikā XXVI.3–8 read verbatim (`phaladeepika:PG322:C1`, `PG323:C1`), L0 `bg_transit_rules` (read-only), why `kala_vedha_gochara` (date grain) is not read, measurement constraint (none) |
| N3 | **PR #2901** — vedha derivation + `vedha_attenuation@1.1.0` + `P2@1.1.0` + pairs accessor + O-VI-6 | head `3515ea074`, **stacked on #2897** (retarget to `main` when #2897 lands) | derivation as half-open span intersection; also the verifier's independent re-derivation; refuses uncited pairs; 8 tests incl. O-VI-6 (abutting obstructors, both exception pairs, node alone, cited-beats-node, half-open edges, not-applicable, missing input); 9/10 mutations caught (survivors output-equivalent) |
| N4 | **`decisions/NATIVE_OPEN_DECISIONS_v1_0.md`** | `campaign/pravaha` | one place for the native's open decisions: **ND-ORB, ND-VIPAREETA, ND-NODE-VEDHA**, the BPHS/Parāśara human re-read. Judge: is each stated honestly, and is the engine's behaviour until ruled (named `unqualified`, never a made-up number) consistent with the code? |
| N5 | **Stream A's window-sweep semantics** (P3/P4) | branch `pravaha/a53-am5-inventory` @ `58a26a020`, brief **Design v1.6** (`A5_3_REGISTERED_WRITER_BRIEF_v1_0.md`) | on the steward's rulings: window = connected union of admitted supports; peak = earliest instant of the max; `score` = max member within-path product (NULL when none qualified); `evidence_for/_against` = per-channel Σ over roots of the per-root max, never netted — **`evidence_against` is the evaluated 0.0 of an empty sum on a qualified window ONLY because P3/P4 records all land in the for-channel and the registry row declares no against-direction operand; NULL when unqualified**; a **mixed window** (some members qualified) scores from its qualified members and discloses the rest through `null_states_used` (**lower-bound marker**); `severity` = NULL always; **kernel read from the factor row** (`applicability.span` ⇒ membership step with the row's `inside`; `applicability.angular` ⇒ the ROW's orb; no `applicability` ⇒ `unqualified (applicability_undeclared)`; null `orb_deg` ⇒ `unqualified (orb_not_ratified)`); path→version taken from the records, nothing binds 1.1.0 until #2897 is accepted; drishti called through an injected source; independent `range_agg` re-check after every grain write; 10 mutations checked. **Judge:** does the stored semantics agree with AM-13/AM-17 and 1156's CHECKs, and does the lower-bound marker honestly carry a mixed window? |
| N6 | **#2894 `graduated_drishti` evaluator — now MERGED** (`8cf6fba6e`) | was OPEN in v1.5 | merged; golden grid 9 grahas × 12 offsets; **no rebase needed** for #2897/#2901 (no file overlap: #2894 touched only `drishti.py` + its test; #2901 reports MERGEABLE/CLEAN) |

## §C. Standing (unchanged from v1.5)
Pre-conditions **PC-1…PC-4**; known limits (database cannot judge the *right* inventory; sealer and verifier principals not provisioned; DB-Integration CI job advisory, `postgres:16`; mutation harness "any test fails" counting; seal cost measured only on synthetic volume; **ND-ORB open**; `'5.0'`/`'4.1'` scorer not run, SI mapping pre-registered against '3.0' knowledge only). Open list: BPHS human re-read; L1 Sun-rūpa finding; AM-12 candidate; YAMAKANTAKA L1 gap; `varga_position` unclassified; combustion Jupiter/Saturn lines; **new:** ND-VIPAREETA, ND-NODE-VEDHA.

## §D. Judge-list for the delta
1. **AM-18 as an amendment to frozen text** (N1, N2): is "zeroes ⇒ excludes" a faithful reading of §2.3 inv 3/§5.2 inv 1 given the cited nullification, and is the fallback (value 1.0 + annotation only) the right alternative? Are the Moon scope and the Mercury exemption correct against Phaladīpikā XXVI.4/.6?
2. **#2901** as code (N3): pairs read not copied and refused when uncited; the exception pairs; node and Moon handling; O-VI-6 adequacy; whether stacking on #2897 is sound.
3. **Stream A's sweep semantics** (N5) against AM-13/AM-17, 1156 and the factor rows #2897 declares — in particular `applicability_undeclared` for the 1.0.0 rows and the `evidence_against` empty-sum rule.
4. **NATIVE_OPEN_DECISIONS** (N4): honest framing of the three ND items.
5. Anything in §A the delta contradicts.

Verdict shape requested: ACCEPT / ACCEPT_WITH_AMENDMENTS / REJECT per N-item, with numbered findings.
