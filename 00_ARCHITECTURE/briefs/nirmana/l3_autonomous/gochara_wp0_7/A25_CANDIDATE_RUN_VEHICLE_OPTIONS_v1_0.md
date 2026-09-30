---
artifact: A25_CANDIDATE_RUN_VEHICLE_OPTIONS
version: "1.0"
status: ACTIVE
date: 2026-09-30
owner: Stream A (Karma) — Pravāha A2.5 re-scoped
authority: steward M20260930T192629-049c (guard NOT extended; century job deleted per #2791; write options, park)
---

# A2.5 re-scoped — vehicle options for the narrowed '4.1' candidate run

Target unchanged: `'4.1'` build for 482012f1 over the scored horizon
1998-01-01 → 2026-04-17, candidate only, never flipped, ADK-0028 (no local
century enumeration). The dedicated Cloud Run job route is closed: the strict
isolation invariant "builder credential/identity on exactly one named job
(`brahma-build-pipeline-job`)" stands, and the native deleted
`brahma-gochara-century-job` (#2791).

## Option A — governed asset build inside `brahma-build-pipeline-job` (recommended)

Run the narrowed build as an **orchestrator asset build** of
`ka_gochara_v3_century_materialize` (a registered orchestrator writer with
asset_id, mutation guard, provenance digest — already the governed production
path for `kala_gochara_windows` '4.x' rows), dispatched through the existing
build-trigger inside the one named build job.

- **Needs (Stream A, code only):** writer support for a narrowed explicit
  horizon + candidate-only generation marker `'4.1'` (never flipped;
  generation-governed check already exists); an asset_registry row / dispatch
  entry for the narrowed run; streaming payload discipline from the #2772
  runner ported into the writer; gates/evidence emitted as today (PRAMĀṆIN,
  `$P metric`).
- **Native-only steps:** none for code or credentials. The build dispatch
  itself is a production write authorization — already covered by D-CLOUD's
  narrowed-run approval; the steward schedules.
- **Cost:** moderate code work, all inside my may-touch scope
  (`pipeline/orchestrator/writers/ka_gochara*.py`, cutover scripts, tests).
- **Security:** zero change to the isolation invariant; no new surface.

## Option B — separate vehicle with its own credential boundary (DP-SD-020)

A new Cloud Run job with a **new, distinct** service account and DB secret
(not the builder pair), the isolation preflight extended to recognise that
new identity as a second, separately-scoped surface, and the deploy step
restored with the new binding.

- **Native-only steps (several):** create the SA, the secret, DB grants
  (credential change — always native); approve the guard extension;
  re-approve the job spec.
- **Cost:** slowest; re-opens the guard that was just affirmed; two builder-
  class surfaces to audit forever.
- Only worth it if Option A's writer adaptation is rejected.

## Option C — defer to the Phase 5 registered writer (A5.3)

Make the narrowed '4.1' build the first execution of the A5.3 registered
writer instead of a bespoke vehicle. Maximally aligned with the campaign's
end-state, but delays A2.6 evidence (benchmarks, gates) until after J1/A5.3.

## Recommendation

**Option A.** It keeps one credential boundary, uses the governed path that
already owns century materialisation, and unblocks A2.6 without any native
credential work. If review shows the century writer cannot carry a narrowed
candidate run cleanly, fall back to C, not B.
