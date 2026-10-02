---
artifact: REVIEW_REQUEST_A5_5_GATE
version: "1.5"
author: "Stream B (Śāstra) — Exec B (Claude Sonnet)"
date: "2026-10-02"
reviewer: "Codex gpt-6-astra (max) — dispatched by the steward"
authority: "Review request only; authorizes nothing."
supersedes: "v1.4. Adds: 1206 v1.2 + its Codex ACCEPT_WITH_AMENDMENTS, migration 1220 (merged), AM-12…AM-17, the SI-mapping pre-registration, ND-ORB, the drishti/AM-13 PRs, and the named pre-conditions PC-1…PC-4."
---

# A5.5 gate — current state (2026-10-02)

## Exhibits

| # | Exhibit | Version / ref | State |
|---|---|---|---|
| 1 | **GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT** | **v0.10** (`campaign/pravaha`) — AM-1…AM-17, PC-1…PC-4 | AM-1…AM-9 **accepted at pre-gate** (v0.5). **Not yet reviewed:** v0.6–v0.10 — AM-10, AM-11, the F-2 binding, the 1206 corrections, v0.8's R6 + version-scope paragraph, **AM-12** (candidate), **AM-13** (RULED: applicability by object kind; classification by geometry), **AM-14** (RULED: Moon-agent edges excluded from the stored enumeration), **AM-15** (RULED: P1 anchor, lagna-inclusive), **AM-16** (RULED: `'5.0'` manifest vector contents), **AM-17** (RULED: stored window fields), and the **PRE-CONDITIONS** section |
| 2 | **PR #2817** — migration 1204 | head `b9d5d2718` | **ACCEPTED** (rounds 3–5 and the 1206 review). OPEN, **HOLD** for the protected window |
| 3 | **PR #2867** — migration 1206 (AM-5 storage + seal checks) | head `fc10a91fe` (v1.2) | **Codex on v1.2: ACCEPT_WITH_AMENDMENTS, no merge-blocking item** (R1–R4, R6 closed; R5 partly — sealer replay EXECUTE, now fixed in the suite). Since that review (test-only): six-table grant matrix + refused operations, sealer replay-helper EXECUTE and the lifecycle's seal and both replays run as the restricted sealer, AM-14 live test; mutation harness 35/35. PR body refreshed (advisory-vs-required stated). OPEN, **HOLD** |
| 4 | **PR #2884** — migration 1220 (builder EXECUTE on 18 contract functions + seal-table SELECT) | merged `dba48ec5c` | MERGED; deployment-faithful role-mirror suite (fails-before / succeeds-after / exact set / each grant necessary). **Not yet reviewed by Codex** |
| 5 | **PR #2897** — AM-13 registry | head `576907611` | `activity_kernel@1.1.0` + `graduated_drishti@1.1.0`, P3/P4/P5 @ rule_version 1.1.0, kernel evaluator; **HOLD until reviewed with this packet**; point branch `unqualified` until ND-ORB |
| 6 | **PR #2894** — `graduated_drishti` evaluator | head `8cf6fba6e` | OPEN, not queued; golden grid 9 grahas × 12 offsets; cites only lines read |
| 7 | Merged code, not yet reviewed: **#2869** (F-4 `sad_bala_sufficient`), **#2871** (F-5 P5 evaluators), **#2881** (F-3 `p6.nakshatra_index`) | merged | ordinary code reviews |
| 8 | `design/IDENTITY_CANONICAL_BYTES_CONTRACT_v1_0.md` | F-3 | §9 updated: version scope now implemented in 1206 v1.2 |
| 9 | `design/WINDOW_SWEEP_ANSWER_v1_0.md` | adopted by the steward (rulings → AM-13…17) | cited answers for Stream A's window sweep |
| 10 | **`measurement/EVALUATION_PROTOCOL_v2_3_ADDENDUM_SI_MAPPING_v1_0.md`** | **pre-registration** | `si := evidence_for`; chosen **after** the '3.0' baseline, **before** any candidate result; **a measurement pre-registration, not a spec item** |
| 11 | `decisions/ND_ORB_DECISION_PACKET_v1_0.md` | for the native | open **native** decision ND-ORB (what orb for true point targets); no measurement run |
| 12 | `measurement/ORACLE_EXECUTION_MAP_v1_2.md`, `design/PREREQUISITE_EVALUATION_ANSWER_v1_0.md` | as v1.4 | unchanged |

## Named PRE-CONDITIONS (draft §"A5.5-gate NAMED PRE-CONDITIONS")

Conditions of **named later steps**, not of merging #2867/#2817. The steward schedules ONE protected window for 1204 + 1206 when Stream A's writer is ready to use them.

| # | Pre-condition | Before |
|---|---|---|
| **PC-1** | Sealer replay-helper EXECUTE; initial seal **and both replays** run as the restricted sealer. **Suite part done** (#2867 head); the real principal's grants and activation remain | the sealing principal is activated |
| **PC-2** | Remaining **F-3** (identity/census, `self`→`native` vector update) + **F-6** (manifest binding, Moon receipts) | writer / serving acceptance |
| **PC-3** | Rehearsal with **real principals**, quiescence, representative volumes, seal latency, rollback / forward-correction (1204 can stay committed if 1206 fails) | the protected deployment |
| **PC-4** | **Distinct verifier principal** (today the verifier runs in the builder's session — steward decision; independence is a process property, not a database one) | verifier independence is claimed |

## Known limits a reviewer should hold us to

* The database cannot judge whether an inventory is the **right** one (verifier's re-derivation, O-RP-9); a shared writer/verifier misreading is a named residual.
* The sealing principal and the verifier principal are **not provisioned** (credential/role creation is the native's).
* The 1206 live suite runs in CI job *DB Integration Tests* on `postgres:16`; that job is **advisory, not a required check**. Production's PostgreSQL version is unverified (≥ 14 needed). The mutation harness counts a mutation caught when **any** test fails (no per-mutation attributed killer).
* Seal cost measured only on a small synthetic generation; production-realistic volume belongs to PC-3.
* **ND-ORB is open**: until the native rules, point targets are `unqualified`; the old 5.0° is not carried forward.
* The `'5.0'`/`'4.1'` scorer has not been run; the SI mapping is pre-registered against '3.0' knowledge only.

## OPEN LIST (recorded, not cited)

1. **Human re-read owed:** BPHS lines the spec/oracles cite for the graduated aspect rule (`BPHS1:16496-16502`, O-CF-DRISHTI; kernel docstring ch.26 śl.6-8) are **not retrievable by verse from the served corpus** (two searches); nothing in #2894/#2897 cites them.
2. **L1 data finding (referred):** `chart_facts` Sun `graha_shadbala_total`/`required_rupa` = 5.0 vs Phaladīpikā IV.22 and BPHS ch.27 śl.32–33 = 6.5; six others agree. Blocks any serving use of `sad_bala_sufficient` (AM-12).
3. **AM-12** (candidate): `sad_bala_sufficient` as a soft factor of a new P1 rule_version — needs this gate + the L1 owner.
4. **L1 gap (YAMAKANTAKA):** stale L1 build (2026-09-07) pre-dates the merged emitter; 8 resonance rows stay `unavailable` until Suvarṇa's S-L1 rebuild + a resonance re-run.
5. `varga_position` is the one DB object kind AM-13 leaves unclassified.
6. Combustion-table Jupiter/Saturn lines (`nadi_navamsa_patel:PG2524` continuation) not retrieved (ND-ORB packet).

## What the next reviewer should judge

1. **AM-13…AM-17 as spec text** (v0.10) against the frozen v1.4 and the applied 1156 schema (score ∈ [0,1]/NULL; evidence unbounded; severity NULL) — is anything contradicted, and is the ORB handling (named native decision, point branch unqualified) honest?
2. **PR #2897 / #2894** as code: classification by geometry (checked against 1155's `kgrr_object_kind_ck`), no caller-supplied orb, drishti golden grid, supersession records.
3. **The SI addendum as a pre-registration:** is the stated provenance (chosen after '3.0', before any candidate result) verifiable and sufficient?
4. **#2867 v1.2 delta since your review** (test-only) and **#2884/1220** (grants).
5. **PC-1…PC-4** — are they the right named gates?

Verdict shape requested: ACCEPT / ACCEPT_WITH_AMENDMENTS / REJECT per exhibit, with numbered findings.
