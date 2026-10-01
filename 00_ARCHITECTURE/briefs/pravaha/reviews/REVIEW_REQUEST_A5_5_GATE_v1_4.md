---
artifact: REVIEW_REQUEST_A5_5_GATE
version: "1.4"
author: "Stream B (Śāstra) — Exec B (Claude Sonnet)"
date: "2026-10-02"
reviewer: "Codex gpt-6-astra (max) — dispatched by the steward"
authority: "Review request only; authorizes nothing."
supersedes: "v1.3 (round-5 state). This version is the packet to attach to the next review and records the state after the 1206 review and the F-3…F-5 work."
---

# A5.5 gate — current state (2026-10-02)

## Exhibits

| # | Exhibit | Version / ref | State |
|---|---|---|---|
| 1 | **GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT** | **v0.7** (`campaign/pravaha`, latest commit on that branch) — AM-1…AM-11 | AM-1…AM-9 **ACCEPTED at pre-gate** (Codex v1.4, reviewed v0.5); **v0.6–v0.7 are NOT yet reviewed**: AM-10 (daśā read-contract re-pin rule), AM-11 (prerequisite-evaluation pins + P1 obligation-agent role token), F-2 exclusion-evidence binding, ledger input-binding, review-driven corrections R1–R5 |
| 2 | **PR #2817** — migration 1204 (`av_qualifier`) | head `b9d5d2718` | **ACCEPTED** by Codex in rounds 3, 4, 5 and again in the 1206 review ("unchanged"); CI green; **HOLD** for the protected window |
| 3 | **PR #2867** — migration 1206 (AM-5 storage + seal checks), stacked on #2817 | head `377c5ce71` (v1.1) | **Codex v1.0: REJECT** (R1–R4 + R5 test gaps) → reworked in place (1206 is applied nowhere); **awaiting Codex re-review**; CI green incl. the new *required* live-DB job; **HOLD** (same protected window as 1204, after it) |
| 4 | **PR #2869** — F-4 `sad_bala_sufficient` v1.0 | head `fd3ce7a6f` | CI green; thresholds corroborated by a second served source (BPHS ch.27 śl.32–33); not yet reviewed |
| 5 | **PR #2871** — F-5 P5 evaluator fixtures | head `9e4e4894e` | CI green; not yet reviewed |
| 6 | `design/IDENTITY_CANONICAL_BYTES_CONTRACT_v1_0.md` | F-3 | NEW — specification of the identity bytes; not yet reviewed |
| 7 | `measurement/ORACLE_EXECUTION_MAP_v1_2.md` | F-5 | NEW — 1205 reference corrected; B6-F16/F17 restated as seam acceptance contracts |
| 8 | `design/PREREQUISITE_EVALUATION_ANSWER_v1_0.md` | adopted by the steward | answers which declared prerequisites are true-by-construction vs independently evaluated |

## Follow-ups F-1…F-6 (Codex v1.4 ranking; owners A = Stream A, B = Stream B)

| ID | Item | Status now |
|---|---|---|
| **F-1** | AM-5 migration + protected wiring + database adversaries | **Implemented (1206, PR #2867); Codex-REJECTED once, reworked, awaiting re-review.** Live suite on a disposable Postgres (real builder/sealer roles, competing-session locks, every table × operation after sealing), 27/27 mutations caught by a reproducible harness run in CI |
| **F-2** | exclusion `basis`/`ruling_ref`/`reason` in the verified preimage | **Spec + 1206 implementation + model + live tests done**; reviewed only as part of the 1206 review |
| **F-3** | identity canonical bytes, storage mapping, class census, version scope, candidate invalidation | **Specified** (contract above). **Open code/migration consequences:** Stream A (`PhysicalObjectId` refuses non-lowercase; point round-trip guard); 1206 (`superseded_by_version` reason, `multiple_included_versions` check, W1 vectors `self`→`native`) — deliberately not applied while 1206 is under review |
| **F-4** | typed operand storage, declaration keys, factor-row `null_state`, edition/translator | **Factor part done (PR #2869):** `null_state` on the factor row, edition/translator identified, raw rūpas as typed unscored evidence. **Open:** durable *storage* of typed operand evidence (relationship record has no evidence field), declaration-key bytes, P5a/P5b applicability storage — A + B |
| **F-5** | actual P5 evaluator fixtures; oracle-map repair | **Done (PR #2871 + map v1.2).** B6-F16/F17 remain strict-xfail on Stream A's branch until the seams exist; acceptance contracts written |
| **F-6** | Moon receipts; generation-5 manifest-digest binding (`inventories_digest`, `moon_on_demand` exclusion) | **Open** (unimplemented) — A + B |

## Known limits a reviewer should hold us to

* The database cannot judge whether an inventory is the **right** one; that rests on the independent verifier
  (O-RP-9). A shared misreading by writer and verifier is a named residual.
* **Sealing needs a separately authorised principal**: 1206 deliberately does not widen the builder (1216 withholds
  INSERT on the seal table). Who that principal is has **not** been decided. The verifier's runtime principal is
  also undefined.
* Production's PostgreSQL version is **unverified** (the seal check needs ≥ 14); CI runs 16, local runs 17.
* Seal cost was measured only on a small synthetic generation (27 classes × 40 obligations: milliseconds); a
  production-realistic volume test remains before any window.
* AM-10 is conditional: it takes effect only when the L1 rebuild closes and carries no pin value.
* A real L1 data discrepancy was found and referred (L1's Sun `required_rupa` differs from both served sources);
  it is recorded, not fixed.

## What the next reviewer should judge

1. **PR #2867 v1.1:** whether R1–R5 are closed in the SQL and the suite (not the narrative) — in particular the full-key
   commitment equality, the bridge binding for publication and partitions, the total pin CHECKs, the session-independent
   digests with the real audit column, and the role/concurrency evidence.
2. **v0.6–v0.7 of the amendment draft** (AM-10, AM-11, F-2, review-driven corrections).
3. **The F-3 contract:** whether its bytes are complete and consistent with 1153/1155 and Stream A's implementation.
4. **PR #2869 / #2871** as ordinary code reviews.

Verdict shape requested: ACCEPT / ACCEPT_WITH_AMENDMENTS / REJECT per exhibit, with numbered findings.
