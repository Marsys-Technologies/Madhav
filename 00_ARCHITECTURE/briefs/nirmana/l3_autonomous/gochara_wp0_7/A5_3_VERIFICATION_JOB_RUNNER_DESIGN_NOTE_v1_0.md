---
artifact: A5_3_VERIFICATION_JOB_RUNNER_DESIGN_NOTE
version: "1.0"
status: "DESIGN ONLY — no code until the native rules on ND-ROLES (option A). Nothing here is decided."
date: 2026-10-02
author: Pravāha Stream A (Exec A), steward M20261002T055158-aac2
changelog:
  - "1.0 (2026-10-02): the runner the ND-ROLES packet (v1.1, option A) describes: entry point, preconditions, sequence, outputs, refusals, tests."
---

# The separate verification job — the runner (design note)

**Why it exists.** The orchestrator hands every writer ONE connection, the builder's; 1240 grants the builder nothing on its verification table and (under option A) 1206 §7's builder grant is removed. So no build step can record a verification result — by design. Verification is a **separate act after the build, under the verifier's own identity**; until it has run the candidate gate stays closed.

## 1. Shape
* **Module** `services/gochara_kernel/verification_job.py` — a pure orchestration LIBRARY taking an open connection (`run(conn, chart_id, generation, *, classes=None, report_only=False) -> Report`), so every refusal and every row is testable on a disposable database.
* **Entry point** `pipeline/orchestrator/verification_job.py` — `python -m pipeline.orchestrator.verification_job --chart <uuid> --generation <g> [--class <c> …] [--report-only]`. It is **not** a registered writer and is not in the build DAG (the frozen contract is untouched, and nothing chains it to the build).
* **Identity.** Reads its database URL from ONE variable (`GOCHARA_VERIFIER_DB_URL`) bound to the verifier's secret; it never reads the builder's. First act: `SELECT current_user` + `has_table_privilege` self-check — **refuse** if the login is the builder, a superuser, or holds INSERT/UPDATE/DELETE on any builder-written `ka_gochara_*` table (the runner proves its own separation before it trusts it). It does not `SET ROLE`.
* **Deployment (steward/owner of deploy, not mine):** a Cloud Run job from the pipeline image with this entry point, its own service account and secret, the secret-isolation gate extended; an operator dispatches it per (chart, generation).

## 2. Preconditions — the runner REFUSES BY NAME and writes NOTHING unless all hold
1. **An unsealed candidate manifest** exists for the generation (`kala_gochara_publication` present, not published; no `ka_gochara_generation_seal` row) — `refused:no_candidate_manifest` / `refused:already_sealed`.
2. **A complete build.** Derived from the data the verifier may read, not from the orchestrator's state: every event class in the manifest's class census has a FINALISED inventory bound to the snapshot, an `event_class` coverage partition that completed the horizon, and every included path grain has its windows; plus the build's own completion marker read from the (verifier-readable) build-state view — the SATYA-DĪPA substep-plan-completeness predicate, not "rows present" (§N.8). Otherwise `refused:incomplete_build` naming the first gap.
3. **Input identity unchanged:** `input_vector_verifier.verify_inputs` re-derives the manifest's AM-16 vector from the verifier's own reads (registry/L0/sky in SQL, files and library by hashing, platform string) — a mismatch is `refused:stale_inputs`, not a verification of stale data.
4. The consumed daśā population is the §4.0 population (`validate_consumed_dasha_population`).

## 3. Sequence (per event class; one transaction per class, replace-before-seal)
1. **Inventory (1206).** `inventory_verifier.derive_class_pins` + `rederive_inventory_digest` + `rederive_ledger_digest` (cuts, resolved agents, the XX.38 delivery obligations) → `write_verification` (the 1206 row).
2. **Records.** `record_verifier.verify_p1_support`, `verify_p1_house_descriptor`, `verify_p1_anchors`; `window_verifier.verify_member_support`, `verify_member_geometry` (independent Swiss probes — needs the pinned `.se1` path and the Swiss-owner discipline).
3. **Windows (1240).** For every (path, rule version) the inventory pins: `window_verifier.verify_window_semantics` → `window_gate.record_verification` (the 1240 row: VERIFIED | UNVERIFIED_DYNAMIC | FAILED, with the digest and policy version).
4. **Gate.** `window_gate.candidate_gate` (the same function the seal uses) → the closing report: which grains are VERIFIED, which reasons keep the gate closed.
Re-runs REPLACE (delete-then-insert) while the generation is unsealed; the write guards refuse after the seal.

## 4. Outputs and exit codes
A JSON report on stdout (per class/path: status, digests, policy version, reasons) and a one-line cockpit string derived from the gate — `BUILT · NOT VERIFIED · gate CLOSED (n)` → `VERIFIED (policy v1, m of m)`. Exit: **0** every required grain VERIFIED · **2** refused by a precondition (nothing written) · **3** a verifier DISAGREES (the FAILED rows are written; the gate stays closed) · **4** privilege self-check failed (nothing written) · **5** unexpected error (transaction rolled back). `--report-only` runs everything but writes no row (for rehearsal and for an operator who wants to look first).

## 5. What changes elsewhere (when ruled)
* The writer's in-build verification persists only when it holds INSERT; under option A it never does, so that branch becomes a report-only note (`verification_pending_verifier_principal`, already today's behaviour for an unprivileged session). The persistence code can then be removed from the builder path — a deletion, proposed with the roles ruling, not before.
* The live suites' `verify` helper switches from the builder login to the verifier role (Stream B's grants migration); the role-mirror tests I already have (faithful roles, seal flows) become the runner's acceptance.
* The cockpit candidate line (derived from the database, not the orchestrator) is the small unbuilt surface the packet names.

## 6. Tests (written when ruled, on a disposable PG15 with the faithful role mirror)
Runner as verifier writes exactly the two verification tables and nothing else · as the builder it self-refuses (exit 4) · refuses without a candidate manifest / on a sealed generation / on an incomplete build / on stale inputs, each writing zero rows · re-run replaces, never accretes · a DISAGREE leaves the gate closed with named reasons · after a full VERIFIED run the seal (as the sealer) succeeds and the generation freezes · `--report-only` writes nothing · no builder credential is ever read (the entry reads one variable).

## 7. Open points for the native / steward
Operator dispatch vs automatic trigger (packet Q3 — recommended: operator) · whether the "complete build" marker is a verifier-readable view or the data-derived check alone (recommended: both, the data-derived check being authoritative) · new `gochara_verifier` vs reuse of `data_plane_verifier` (packet: new).
