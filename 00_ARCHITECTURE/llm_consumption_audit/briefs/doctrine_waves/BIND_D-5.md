---
artifact: BIND_D-5
type: BINDER PASS RECORD
wave: D-5 — Gochara-Chitra
status: BOUND
bound_on: 2026-07-19T08:31:47Z
binder: Sonnet 5 conductor session (fresh worktree wave/D-5/conductor, cut from origin/main c8801e17)
governing: CONDUCTOR_PROTOCOL.md, ESCALATION_POLICY_v1_0.md, ADJUDICATOR_CHARGE_v1_0.md, BRIEF_D5.md v1.0 FROZEN
---

# BIND_D-5 — Binder pass, D-5 wave open

## §1 — Pre-open reconciliation (this session's own state, recorded per native instruction)

The launching checkout (branch `pg1/wave`) held stale local D-5-prep artifacts predating PR
#617/#618. `origin/main` (`c8801e17`) was independently confirmed clean: `current_wave: D-5`,
`BRIEF_D5.md` v1.0 FROZEN, `REPORT_D-4A.md`/`STATE_D-4A.md` present. Root cause: stale local
checkout, not a false readiness-pass report (all 7 of 8 untracked docs were byte-identical to
`main`; the 8th, `BRIEF_D5.md`, was the pre-freeze v0.1 skeleton, superseded). No push to `main`
was required. This wave conducts from a fresh worktree (`wave/D-5/conductor`) cut from `origin/main`
specifically to avoid entangling with `pg1/wave`'s own legitimate, unrelated, uncommitted PG-2
diagnostic work — same precedent D-4a's own close report (§7) recorded for the same reason.

## §2 — Gate-zero (protocol §0 precondition for SPAWN)

- `ref_planet_transit_get` (Sun, 2026-07-19→20): **200 OK, no 401.** PASS.
- `kala_temporal_bundle` (482012f1, 2026-01-01→2027-01-01): `sidecar_available: true`,
  `convergence_windows` populated. PASS.

**Gate-zero: HOLDS.**

## §3 — First actions (native directive, both dispositioned before SPAWN)

**CR-113 (orphaned `build_runs` row).** Row `372b5cfa-9aa6-45b7-b72f-dcb813e57f7b` (D-3-era,
`state='running'` since 2026-07-18T12:36, `ended_at=NULL`) confirmed live via read-only query.
Reconciled via the platform-owned path: `POST /api/cockpit/watchdog` on the deployed `amjis-web`
connector (`x-watchdog-auth` secret read from the service's own live Cloud Run env config — same
plaintext-secret hygiene gap already logged in protocol §8.1, not introduced by this action).
Result: `{"orphan_runs_failed":1,...}`. Re-queried: row now `state='failed'`,
`ended_at='2026-07-19T08:30:56.422Z'`. **CLOSED — orchestrator untouched, no manual DB write.**

**CR-114 (mcp/sidecar/job images stale vs `origin/main`).** Live-checked: `amjis-web` now matches
`origin/main` HEAD exactly (`c8801e17`, deployed by #618). `amjis-mcp`/`amjis-sidecar`/
`brahma-build-pipeline-job` remain pinned at `8f3ace37`/`e995c498` — **confirmed still inert**:
zero commits between those SHAs and `c8801e17` touch `platform-mcp/` or `platform/python-sidecar/`
(re-verified this session, same finding as the pre-D-5 readiness pass).
**Adjudicator-engineering ruling (ADJUDICATOR CHARGE §2 loop, recorded here per protocol §8.8.ii
single-writer):** decision = whether to force an out-of-band `workflow_dispatch` deploy now vs.
rely on `deploy.yml`'s existing per-path `workflow_run` trigger. Ruling: **rely on the standing
trigger — no preemptive out-of-band deploy.** Reasoning: protocol §8.3 reserves `workflow_dispatch`
(bypasses CI) for rollback-class fixes with sign-off; this is a routine resync with zero functional
gap today, and `deploy.yml` already fires automatically, CI-gated, on the FIRST merge that touches
`platform-mcp/**` or `platform/python-sidecar/**` — which is exactly G-2's/G-3's own merge. Forcing
a no-op redeploy now buys nothing G-2/G-3's own merge doesn't already guarantee, and skips the CI
gate for no reason. **Falsifier: if G-4's live-verification step for G-2/G-3-authored sidecar code
fails specifically because the serving image predates the merge that shipped that code — impossible
under the standing trigger, since deploy fires ON that merge — reopen this ruling.** Not blocking;
routed around per §1 (engineering fork, non-PARK, non-§2).

## §4 — BRIEF_D5.md §B slot re-confirmation (same-day; re-confirm-not-rederive per protocol §2.1)

Same UTC day as the pre-D-5 readiness pass (2026-07-19) that populated §B.1–§B.6. Live re-checks
performed this pass: §B.5 substrate health — `sidecar_available: true` (§2 above, fresh); CR-113
now additionally CLOSED (was open at readiness-pass time, per §3 above — an improvement on the
readiness snapshot, recorded, not silently inherited stale). §B.1–§B.4, §B.6 not re-derived from
scratch (protocol's own instruction: re-confirm holds, not re-derive) — no intervening deploy or
estate change occurred between the readiness pass and this Binder pass (only the watchdog
reconcile, which is additive/corrective, not estate-altering in a way that would invalidate those
slots). **All §B slots: CONFIRMED HOLDING.**

## §5 — Rollback pin (protocol §2.1 / §6.1)

```yaml
rollback_pin:
  amjis_web: c8801e17bcd28b503cbeeac16533cc713124a251
  amjis_mcp: 8f3ace3756c219a65fe8d3baee96606092a38913
  amjis_sidecar: e995c4981068eabf987ac40197749177cd91a239
  brahma_build_pipeline_job: e995c4981068eabf987ac40197749177cd91a239
  abhisek_build_id: d2470804-8aba-478a-9407-69ef9b559c68  # last completed run, 2026-07-18T22:28:12Z
```

## §6 — Rebuild scope (protocol §8.2, Binder records at open)

Expected: `scope=asset_set` targeting the new `ka_gochara_sweep` writer (G-4) ONLY once it exists
— G-1/G-2/G-3/G-5 are pure service/schema/ledger work, no orchestrator asset, no rebuild trigger.
No full-L1→L5 trigger identified (no new L1 fact category, no shared-substrate change, no
existing-column semantic change — BRIEF_D5 §1 confirms this framing). Binder will re-confirm the
exact `scope_target` asset list at G-4's INTEGRATE step once the new writer/migration exist.

## §7 — Disposition

Brief stamped **BOUND**. SPAWN authorized (protocol §0 auto-proceed: clean Binder pass + gate-zero
both hold).
