---
artifact: T2_GATECHAIN_PRESTAGE_README
canonical_id: T2_GATECHAIN_PRESTAGE_README
version: 1.0
status: PRE-STAGED — index of everything Track T2 prepared ahead of SESSION-A-SWEEP's
  SWEEPS-COMPLETE signal. Nothing indexed here has been executed against real sweep
  data; it is staged so the gate chain is a RUN, not a DISCOVERY.
created: 2026-08-05
author: Track T2 builder (gate-chain pre-staging lane, ṢAḌ-DARŚANA overnight campaign)
governing: SHAD_DARSHANA_NIGHT_RUN_v1_0.md (orchestration) + SHAD_DARSHANA_BRIEF_v2_0.md
  §3 Gate W2/Gate W3 (execution contract, verbatim source for the two checklists) +
  SHAD_DARSHANA_STATE.md (ledger — NEXT-ACTION is the gate-chain's own authoritative
  sequence and current sweep progress)
---

# Track T2 — gate-chain pre-staging, index

This directory (and its two sibling script locations) is the output of Track T2: a small,
independent lane whose only job was to make sure that when SESSION-A-SWEEP's ledger shows
`SWEEPS-COMPLETE`, the Conductor session that picks up the gate chain has to **run** things,
not **discover** them. Track T2 never touched SESSION-A-SWEEP's dispatch, safety net, or
ledger entries, and dispatched nothing against production.

## The gate chain this pre-staging serves (verbatim from `SHAD_DARSHANA_STATE.md` NEXT-ACTION)

> S4-05 re-test on real data → field build both charts → hash-replay → weights v0 →
> FIRST skill score published (permanent CI baseline) → GOF → one integration→main PR
> (merge queue; queued-green 5–60 min is normal) → deploy → PARĪKṢAKA both charts →
> Gates W2/W3 full-criteria evaluation.

**This fires ONLY on SESSION-A-SWEEP's own `SWEEPS-COMPLETE` ledger signal — do not start it
early, do not poll Session-A's rows** (standing instruction, still in force as of this
pre-staging pass; sweep progress at last check: 482012f1 495/606, 1c826d5a 463/606).

## What is staged, and where

| Gate-chain step | Staged artifact | Status |
|---|---|---|
| S4-05 re-test on real data | `platform/python-sidecar/scripts/s4_05_data_real_retest.py` | Written, syntax-checked, exits code 3 cleanly with no `DATABASE_URL` (confirmed). Ready to run against production the moment SWEEPS-COMPLETE lands. |
| Field build both charts | `platform/scripts/dispatch_gatechain_field_build_482012f1.py` + `..._1c826d5a.py` | Written, syntax-checked. **NOT executed** — per instruction, these are staged only. |
| Hash-replay | No separate script staged — see note below. | Mechanism already implemented (E5, `field_snapshot_id`); the W2 checklist (item W2.1) is how it gets verified, not a script this lane needed to write. |
| Weights v0 | `platform/supabase/migrations/491_kala_field_weights_seed.sql` | **Already exists and is already seeded** — see the "weights-v0 finding" section below. Nothing to stage; this is a verification result, not a gap. |
| First skill score + GOF published | `platform/python-sidecar/scripts/dryrun_skill_gof_synthetic.py` | The harness itself (`services/mi_bhara/skill.py` + `gof.py`) dry-run on synthetic data, confirmed to run end-to-end with no exceptions (see "skill-score/GOF dry-run" section below). This does NOT publish a real score — that still requires the real field build. |
| PARĪKṢAKA both charts | `PARIKSHAKA_W2_ACCEPTANCE_CHECKLIST_v1_0.md` + `PARIKSHAKA_W3_ACCEPTANCE_CHECKLIST_v1_0.md` (this directory) | Literal markdown checklists, every row traced verbatim to the brief's own Gate W2/W3 acceptance text. Ready to walk. |
| Gates W2/W3 evaluation | Same two checklists — each ends in an "Overall Gate disposition" table. | Ready to walk. |

## Weights-v0 finding — NOT a gap (verified existing)

Task item 3 asked me to search migrations/seed data for a `weights_v0` seed and report a real
gap if missing. **It is not missing.** `platform/supabase/migrations/491_kala_field_weights_seed.sql`
seeds exactly this, under the id `v0_classical`:

- `kala_field_weight_versions` row `version_id='v0_classical', status='active', scope='global'`
  — the structural-prior θ⁰ vector, explicitly NOT a fit (`fit_loglik`/`holdout_loglik` are
  honestly `NULL`, `n_events_used=0`).
- `kala_field_weights` rows for every `w_s:<system>` (Law-2 clock exponents), `d:<level>`
  (level-depth weights), `beta:x1..x12` (the twelve frozen log-linear covariates), and
  `rho:<vighna_class>` (thinning strengths) — each `weight_value == prior_value` by
  definition at v0 (`n_eff=0 ⇒ φ̂ = φ⁰`).
- The migration is explicitly the **acyclicity keystone** (brief §2.5 item 4): seeding v0 BY
  MIGRATION, not by a writer, is what lets `ka_kshetra` never list `mi_bhara` in `depends_on`
  — every chart's first `ka_kshetra` build finds an ACTIVE weights version with no writer
  ordering dependency.
- `ON CONFLICT DO NOTHING` idempotency (deliberately `DO NOTHING`, not `DO UPDATE` — re-running
  the migration must never silently overwrite a weight a later `mi_bhara` release changed).

**Production status:** this migration shipped as part of Night 2's W2 build lanes — migration
491 is Lane C's (PR #949, "stages 4–5 field assembly + provenance"; the renumbering record in
this ledger file's "Migration range reserved" section confirms Lane C claimed 491–494, with 491
specifically the weights seed). The Night-4 morning report states `main == production`
now carries "all of Night 2's W2 build lanes" — so `v0_classical` should already be live in
production. **Re-confirm this directly before relying on it** (a direct `SELECT version_id,
status FROM kala_field_weight_versions WHERE version_id='v0_classical'` against production is a
30-second check and costs nothing to run before the field build) — this pre-staging pass did
not have a live `DATABASE_URL` to confirm from inside the sandbox, so the finding rests on the
migration file + ledger citations above, not a live query. This is disclosed, not glossed over.

## Skill-score/GOF dry-run — confirmed working, on synthetic data only

Ran (not just written) `platform/python-sidecar/scripts/dryrun_skill_gof_synthetic.py`, which
exercises the real `services/mi_bhara/skill.py::compute_skill`/`aggregate_chart_skill` and
`services/mi_bhara/gof.py::compute_gof` — the exact functions `mi_bhara`'s stage 9 calls —
against a hand-fabricated two-class synthetic point process (one with real epoch-clustered
structure, one flat/noise). Output (abbreviated):

```
[signal_class]  n_events=18   skill: score=+1.7166 state=established   gof: state=pass
[noise_class]   n_events=12   skill: score=+0.0000 state=not_established gof: state=pass
[chart-level]   n_events=30   score=+1.0300 state=established
HARNESS RAN END-TO-END WITHOUT ERRORS.
```

Exit code `0`. Both `services/mi_bhara/skill.py` and `services/mi_bhara/gof.py` are pure
functions (no DB, no clock — only a seeded RNG for the bootstrap), so this dry-run needed no
database and touched nothing real. The existing unit suites (`tests/l5/test_mi_bhara_skill.py`,
`tests/l5/test_mi_bhara_gof.py`, 30 cases) were also re-run and pass (`30 passed in 0.83s`) —
this dry-run script is a human-readable companion to those, not a replacement.

**This proves the harness runs, not that the real field has skill.** The real skill-score/GOF
publish still requires the real `ka_kshetra`/`mi_bhara` field build on real production data,
which is exactly what the staged dispatch scripts above are for.

## Confirmation: SESSION-A-SWEEP was not touched

This lane worked entirely inside a fresh worktree (`.worktrees/shad-darshana-t2-gatechain`,
branch `shad-darshana/t2-gatechain-prestage`, off `origin/shad-darshana/integration`). No file
under SESSION-A-SWEEP's operational area was read, written, or referenced for anything other
than citation:

- The sweep dispatch scripts (`dispatch_int929_gochara_resume_{482012f1,1c826d5a}.py` etc.)
  are, per `SHAD_DARSHANA_STATE.md`'s own note, "NOT committed anywhere (one-off operational
  scripts, live only in the main repo checkout's `platform/scripts/`, untracked there too)" —
  they do not exist in this worktree at all, so there was nothing to touch even by accident.
- No sweep dispatch, stop, or ledger-entry edit was performed. This lane's own dispatch scripts
  (above) target `ka_kshetra`/`mi_bhara` only — never `ka_gochara_sweep` — and were written,
  syntax-checked, and left **unexecuted**.
- `SHAD_DARSHANA_STATE.md` itself was read-only for this lane (cited extensively above for
  context); no edit was made to it or to any other campaign ledger file.

## Next-session usage

1. Confirm `SWEEPS-COMPLETE` in the ledger (SESSION-A-SWEEP's own signal — do not infer it from
   substep counts alone; wait for the explicit ledger entry).
2. Run `s4_05_data_real_retest.py` (item 9's gate clause) — first, per the ledger's own ordering.
3. Run the two `dispatch_gatechain_field_build_*.py` scripts (after re-confirming the
   preconditions documented in their own module docstrings — L0 substrate live, migration 491
   applied, both charts' sweep genuinely complete including 1c826d5a's horizon-parity ticket).
4. Confirm hash-replay determinism (re-run `ka_kshetra` once more on identical inputs, compare
   `field_snapshot_id`) and the LEL-invariance CI test, per W2 checklist items W2.1–W2.2.
5. Confirm `mi_bhara` published a real skill score + GOF for both charts (first publish becomes
   the CI baseline) — this is the REAL, non-synthetic version of the dry-run above.
6. Open the one `shad-darshana/integration` → `main` gate-close PR, ride the merge queue
   (5–60 min is normal), deploy, confirm traffic tracks latest.
7. Walk `PARIKSHAKA_W2_ACCEPTANCE_CHECKLIST_v1_0.md` then
   `PARIKSHAKA_W3_ACCEPTANCE_CHECKLIST_v1_0.md` against live production, both charts.
