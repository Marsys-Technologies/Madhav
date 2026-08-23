---
artifact: EKV_CONTROLS_CI_WIRING_HANDOFF
version: 1.0
status: PARKED — not a PARISESA lane, kept for a future campaign
author: INTEGRATOR (PARIŚEṢA)
date: 2026-08-16
disposition: SUTRADHARA — new mechanism/architecture question, not a sibling site of an
  already-diagnosed defect; per established precedent (new mechanism = handoff note, not
  a new lane), not spun up as a PARISESA lane.
---

# `ekv_controls.py` is never invoked by CI — handoff note

## What was asked

S6's F-141 work (PR #1312) found that `ekv_controls.py`'s F-102 control (asset_throughput
no-op-completion guard, widened by PAR-R-9 to check `state IN ('lit','mature')`) is not
referenced by any `.github/workflows/*` file. SUTRADHARA asked INTEGRATOR to assess
whether wiring F-102 — or the CL-00 battery more generally — into an actual CI gate step
would be a small, safe addition foldable into normal merge/deploy work.

## What was found (independently verified, not inherited)

1. **The gap is broader than F-102 specifically.** `grep -rl ekv_controls
   .github/workflows/*.yml` returns zero matches. The entire 27-control battery
   (`platform/scripts/governance/ekv_controls.py`) has never been wired into any GitHub
   Actions workflow — not just the one control PR #1312 touches.

2. **This is by design, not an oversight.** `/Users/Dev/shad_overnight/ekv_sentinel_kickoff.md`
   (SENTINEL's own standing kickoff, native's local orchestration scaffolding — not
   committed to this repo) specifies SENTINEL's continuous loop runs `ekv_controls.py`
   manually in a fresh shell against a live `db_url`, on a ~20-minute cadence and after
   every deploy marker. PARISESA's own INTEGRATOR deploy liturgy ("run CL-00 cheap
   subset" per merge batch) is the same pattern. The battery was architected as a
   human/agent-run post-deploy check against real, chart-scoped data
   (`asset_throughput`, `kala_field`, etc.) — not as a CI step.

3. **A smaller, separable, genuinely actionable gap exists independent of CI-wiring
   entirely:** F-102's registry entry is `("F-102", False, True, False, _check_f102)` —
   `cheap=False`. `CHEAP_IDS = {"F-75","F-76","F-83","F-84","F-85","F-87","F-96","F-91"}`
   does not include F-102. So even INTEGRATOR's own `--cheap` per-batch invocation
   silently skips F-102 today, regardless of any CI question. This is a one-line fix
   inside `platform/scripts/governance/ekv_controls.py`, which is S6_ADHARA's leased file
   (`LEASES.json`), not INTEGRATOR's — routed to S6 as a cheap addendum to their F-141/
   #1312 work rather than edited here.

## Why CI-wiring itself was NOT built here

Two things stood in the way of treating this as a small fold-in, independent of size:

- **No lease.** `.github/workflows/**` is not in any of the six streams' `OWNS` lists in
  `LEASES.json` — nobody currently has write authority there under this campaign's rules.
- **A real, undecided infra/security question.** Wiring the battery (or even just F-102)
  into an actual workflow step means either (a) exposing a live/production-scoped DB
  credential to a GitHub Actions runner — a real security decision, not a config
  tweak — or (b) running it against the ephemeral throwaway Postgres `ci.yml`'s DB
  Integration Tests job already uses, which would not contain the real chart-scoped data
  most of these controls actually check, making the check largely meaningless there.
  Neither option is a "small, safe addition" — both are new mechanism decisions.

Per SUTRADHARA's own established precedent for this campaign — a new mechanism/
architecture question is a handoff note, not a new PARISESA lane — this was not built,
not spec'd, and not spun into a D→S→R→B→V lane. INTEGRATOR declined to decide the
underlying security/architecture question unilaterally.

## For whoever picks this up next

Two independent questions, worth separating if this is revisited:

1. **Should `ekv_controls.py --cheap` run in CI at all**, or is the SENTINEL/INTEGRATOR
   manual-against-live-DB pattern actually the correct design (the controls are about
   real production/chart state, not something a fresh ephemeral CI database could
   meaningfully assert)? This is a design call, not just a wiring gap — it may be that
   nothing is actually missing here.
2. **If yes, what DB does it run against and how is the credential scoped/secured** —
   this needs its own answer before any workflow YAML is written, not a `secrets.DB_URL`
   sprinkled in without deciding on it up front.

Reproduction commands, for whoever re-derives this rather than inheriting the note:

```
grep -rl ekv_controls .github/workflows/*.yml   # empty — the finding above
grep -n "CHEAP_IDS" platform/scripts/governance/ekv_controls.py   # F-102 not present
```
