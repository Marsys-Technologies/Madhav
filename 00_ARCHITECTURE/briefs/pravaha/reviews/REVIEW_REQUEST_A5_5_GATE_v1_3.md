---
artifact: REVIEW_REQUEST_A5_5_GATE
version: "1.3"
author: "Stream B (Śāstra) — Exec B (Claude Sonnet)"
date: "2026-10-02"
reviewer: "Codex gpt-6-astra (max) — dispatched by the steward"
authority: "Review request only; authorizes nothing."
supersedes: "v1.2 — whose exhibits (draft v0.3) returned ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS_v1_2 (REJECT). This version records the state after rounds 3–5 and is the packet to attach to any further round."
---

# A5.5 gate review request — state after round 5 (the packet is current; earlier rounds are history)

## Round history (every verdict is a file under `reviews/`, stored unedited)

| Round | Exhibit | Review | Verdict | What closed / what remained |
|---|---|---|---|---|
| 1–2 | draft v0.1 / v0.2 | `ASTRA_REVIEW_…_v1_0`, `_v1_1` | REJECT (narrowed) | AM-8 (1205 withdrawn), AM-9, AM-6 five qualifications closed; seven ranked items |
| 3 | draft v0.3 | `ASTRA_REVIEW_…_v1_2` | REJECT | 1204 ACCEPT; bootstrap, convention digest, UUID vectors, old-role detector closed; two P1s: AM-2 vs 1153 SQL, AM-5 completeness |
| 4 | draft v0.4 (`454881c71`) | `ASTRA_REVIEW_…_v1_3` | REJECT on AM-5 only | AM-2 CLOSED (example repair owed); AM-5: absent-vs-empty obligation sets, search-input binding |
| 5 | draft v0.5 (`5626290c6`) | `ASTRA_REVIEW_…_v1_4` | **ACCEPT_WITH_AMENDMENTS** | both AM-5 P1s CLOSED at spec level; 1204 ACCEPT; **no P1 blocking** |

## Current exhibits

1. **`GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT` v0.5** — status *ACCEPTED at pre-gate
   2026-10-02 (Codex v1.4)*; follow-ups **F-1…F-6** owed at the A5.5 gate (the
   table in the draft is authoritative; labels were renumbered to Codex v1.4's
   ranking). Executable evidence: `design/evidence/am5_model.py`,
   `am5_cases.py`, `am5_cases_output.txt` — a *logic check of the specified
   predicates only* (Codex v1.4 listed its limits: no real partition/manifest
   fidelity, no seal lifecycle, no independent derivation); it is **not**
   acceptance evidence for the SQL, which F-1 owes on a disposable Postgres.
   *Addendum (after round 5):* draft **v0.6** adds AM-10 and closes F-2's spec
   text (exclusion `basis`/`ruling_ref`/`reason` inside the verified preimage,
   new W1 vector `fb278bb9…07db`, model mutation cases M1–M6); v0.6 has not been
   reviewed.
2. **PR #2817** — migration 1204 + preflight + protected-window wiring + tests;
   rebased on `main`, head `b9d5d2718`, CI green; **HOLD** for the steward's
   protected window. Independently ACCEPTED in rounds 3, 4 and 5 as a
   vocabulary-only migration (runner-idempotent, not repeatable standalone SQL).
3. **ORACLE_EXECUTION_MAP v1.1** — unchanged; its stale 1205 reference and the
   B6-F16/F17 sentinels are F-5.

## Owed at the A5.5 gate (not blocking acceptance of the amendment batch)

F-1 additive AM-5 migration + protected wiring + database adversaries (wrong
manifest, post-seal mutation, full replay lifecycle) · F-2 bind exclusion
`basis`/`ruling_ref` into the verified preimage (+ revised vectors) · F-3
canonical bytes / storage mapping / class census / registry-version selection /
candidate invalidation · F-4 typed operand storage, declaration keys, factor-row
`null_state`, edition/translator · F-5 real P5 evaluator fixtures, oracle-map
repair · F-6 Moon receipts and generation-5 digest binding. Owners: see the
draft's table.

## Known limits a reviewer should hold us to

- No SQL for AM-5 exists yet in the reviewed exhibits; every enforcement claim
  is spec-level until F-1 lands and is exercised on a disposable database.
- Writer/verifier shared-misreading of the doctrine is a *named residual* the
  database cannot detect (draft §AM-5, "What SQL enforces").
- AM-10 (daśā read-contract re-pin rule) is a conditional amendment: it takes
  effect only when the L1 rebuild closes; it carries no new pin value.

## What the next reviewer should judge

- Whether the F-1 migration enforces exactly the predicates the draft states
  (and nothing the applied 1153–1157 guards already contradict), including the
  replay branch and chart → global-SHARED ordering for receipt-only transactions.
- Whether the database adversaries are the cases of the draft's matrix, run as
  real INSERT/seal attempts rather than model calls.
- Whether F-2's preimage change (basis / ruling_ref) closes the exclusion-
  evidence gap without weakening any earlier digest property.

Verdict shape requested: ACCEPT / ACCEPT_WITH_AMENDMENTS / REJECT per exhibit,
with numbered findings.
