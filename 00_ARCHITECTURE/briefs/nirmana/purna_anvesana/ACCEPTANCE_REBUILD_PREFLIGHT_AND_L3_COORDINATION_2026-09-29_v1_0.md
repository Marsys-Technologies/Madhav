---
artifact: PURNA_ACCEPTANCE_REBUILD_PREFLIGHT_AND_L3_COORDINATION
version: 1.0
status: PREFLIGHT_PREPARED_OWNER_SURROGATE_RULINGS_ACTIVE
date: 2026-09-29
campaign_id: madhav-purna-anvesana
phase: ACCEPTANCE_AND_LIVE_CLOSURE
authority: Native decision 2026-09-29 on Packet A/B gates (Decision 2, Option A)
governing_brief: 00_ARCHITECTURE/briefs/nirmana/PURNA_ANVESANA_ACCEPTANCE_AND_LIVE_CLOSURE_v1_0.md
prior_findings: ACCEPTANCE_PACKET_A_B_DIAGNOSIS_2026-09-29_v1_0.md
canonical_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
protected_main_at_preparation: 55ec5e3555a8bf2b4a3ed4f42397f03a56396b2d
deployed_web_revision: 55ec5e3555a8bf2b4a3ed4f42397f03a56396b2d
deployed_mcp_sidecar_revision: 205a62618182a73f45a9bee34f8ffff8cdce8892
rebuild_started: false
candidate_validation: NOT_RUN
live_validation: NOT_RUN
campaign_completion: NOT_EARNED
---

# Rebuild preflight and L3 coordination request

All observations below are read-only, taken 2026-09-29 from production metadata, Cloud Run, Git and
GitHub. No rebuild, SQL write, credential change or migration was performed.

## 1. Non-mutating Packet B results

| Check | Result | Evidence |
|---|---|---|
| Served-generation identity | **Partly resolved.** Raw door reports `chart_build_id = generation:sha256:c33e2359…4d0d34`; 9 receipt-bearing assets are unresolved | exact `RESOLVER_SQL` expansion (`served_generation.ts`) run read-only |
| `ga_strength` receipt | **FAIL** — receipt is `proven`/`fresh` but issued under the spec retired 2026-09-19T23:47Z (`receipt_spec_retired`); a new active spec exists, no receipt under it | `asset_output_digest_specs`, `asset_provenance_receipts` |
| `ga_positions` | **FAIL** — `__whole_asset__` partition receipt `unknown`/`stale` (2026-09-07); partial partition receipt predates the spec retired 2026-09-07 | same |
| Dasha binding | `ga_dashas` resolves (`skip_no_delta`, writer run proven). Binding is intact at receipt level but sits on top of an unresolved `ga_positions` | resolver output |
| Replacement/orphan fence | **Not falsely active.** Zero `building` asset rows; zero `intervening_attempt_unreceipted` verdicts. Old terminal `error`/`aborted`/`queued` rows exist under failed/stopped runs (historical, not blocking) | `build_run_assets`, `asset_throughput` |
| Near-miss | **Not available and not ratified.** `notably_absent_yogas` is an honest `not_computed` (`register_d9_judgment.ts`); candidate PR #2705 is open/unmergeable; decision packet (Addendum §6/§11.2) has no recorded ratification | source + docs |
| Timing evidence | **Not fully available.** `ka_dasha_kala` (`receipt_not_proven`) and `ka_gochara` (`receipt_not_fresh`) are unresolved; 11 `ka_*` are stale/error in readiness | resolver + `asset_throughput` |
| Capability snapshot | **Consistent.** Raw contract `capability_content_hash sha256:9b47461d…955f58`, `planner-scu-v2` equals the generated snapshot on this branch | `inquiry_start` vs `capability_knowledge.snapshot.json` |
| Expected-revision config | Portal, managed and raw all report `deployed_revision 55ec5e3` (MCP/sidecar images are `205a626` with no `platform-mcp` diff). Config pins `door_expected_revisions` = `55ec5e3` for all three | `inquiry_start`, Cloud Run |

Unresolved (resolver verdict): `ga_positions` (not proven), `ga_strength` (spec retired),
`bo_cgm_motifs`, `bo_laksana`, `bo_sangati`, `bo_upaya` (not proven), `bo_samvada` (not fresh),
`ka_dasha_kala` (not proven), `ka_gochara` (not fresh).

## 2. Affected assets and why a full coherent rebuild is required

- **Readiness `not ready`:** 42 active per-chart assets non-lit (11 `bo_*` stale, 11 `ka_*`
  stale/error, 11 `mi_*` error/stale/dormant, 9 `ph_*` stale); latest run is a failed, never-dispatched
  `ga_positions` rebuild from 2026-09-19.
- **Dependency order (frozen orchestrator plans it; not hand-ordered):** L1 `ga_positions` →
  `ga_strength` and other `ga_*` dependents → L2 `bo_*` (`bo_laksana` root → `bo_sangati`,
  `bo_upaya`, `bo_samvada`, `bo_cgm_*` …) → L3 `ka_*` → L4 `ph_*` → L5 `mi_*`.
- **Why full, not per-asset:** the two L1 defects sit at the root of the DAG. Rebuilding
  `ga_positions`/`ga_strength` re-generates `chart_facts` and invalidates every downstream L2–L5
  receipt (stale-by-upstream). A partial rebuild would leave the chart in a mixed-generation state,
  which is exactly what served-generation fencing refuses. Repairing only the nine unresolved assets
  would still leave 33 stale/error assets and `CHART_RECOMPUTE_REQUIRED` on the managed door.

## 3. Preconditions that are NOT yet met

### 3.1 L3 coordination (Decision 2 item 3)

| Required condition | Status | Evidence |
|---|---|---|
| Intended L3 source merged to protected `main` | **NOT MET** | #2731 (`l3/gochara-autonomous-wp0-7`, 100 commits, BLOCKED, updated today), #2715, #2717, #2695 open |
| Intended revision deployed | **NOT MET** | web `55ec5e3` lacks all of the above |
| L3 owner reports no active conflicting build/data mutation | **NOT REPORTED** | no lease row for L3 since `MADHAV-L3-KALA-W1-DISPATCH-20260920` (RELEASED); #2731 states a standing order of no build runs and a later resonance rebuild at WP10 step 6 |
| Canonical chart eligible for a coherent rebuild | **NOT MET** | see 3.2 |

### 3.2 Hazards found (must be resolved by the owners, not by this campaign)

1. **Production schema is ahead of deployed source for L3.** `_migrations_applied` contains
   L3-authored migrations 1080–1084, 1087 (2026-09-24) and 1150 (2026-09-28 16:20Z), whose source
   files exist only on the unmerged #2731 (also 1071/1072/1086/1091 there, unapplied). A rebuild on
   `55ec5e3` would run writers that do not match that schema.
2. **`ga_strength` will change again.** #2731 carries migration 1086
   (`ga_strength_contributor_digest_spec`, G-10 per-contributor BAV facts), which would retire the
   spec Purna's 1042 just activated. Rebuilding `ga_strength` before it lands invalidates the rebuild.
3. **Near-miss producer must precede the rebuild.** `bo_laksana` is where the ratified near-miss
   absence signal is produced (Addendum §6). Without it merged and deployed first, the single
   authorized rebuild would still leave the wealth contract unmet and force a second rebuild.
   Owner-Surrogate Ruling OSR-001 owns the candidate set, eligibility rule, and qualification
   language; no Native response is required.
4. **`data_plane_builder` grants:** #2717 (1073/1074, builder read grants/timeouts) is unmerged and
   unapplied; L3 assets that read `bg_synthetic_cohort*`, `bg_transit_moorti` cannot run as the
   builder until it lands.
5. **Open L0 blocker:** `MADHAV-JATAKA-BG-TRANSIT-REPAIR-20260928` is ACTIVE past expiry
   ("root-cause investigation; no production mutation yet") for a `bg_transit_rules` /
   `gochara_resonance_map` FK blocker. A full rebuild includes `ka_gochara_resonance`.

### 3.3 Execution mechanism

- The governed full rebuild is `POST /api/cockpit/runs` (frozen manifest + digest → Cloud Run job
  `brahma-build-pipeline-job`). It requires a `super_admin` session with `write` permission on the
  chart. The probe account is `view`-only and this campaign holds no super-admin credential; minting
  one is out of authority. **The trigger must therefore be issued by the Native from the cockpit, or
  under an explicit, separate authorization for a minted super-admin session.**
- `platform/scripts/dispatch_frozen_rebuild.py` is single-asset only and is not the full-rebuild path.
- A coordination lease on `origin/campaign-coordination` is required (production orchestrator
  rebuild = surface 1 of the dual-campaign plan). No unexpired lease is held by anyone today.

## 4. Rebuild preflight record (to be completed at start)

| Item | Value |
|---|---|
| Source revision | protected `main` tip at start, deployed and read back from Cloud Run |
| Chart | `482012f1-710e-4a25-994a-93821f5871aa` only |
| Orchestrator | FROZEN contract unchanged (`ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md`); no contract edit |
| Expected effects | per-chart delete-then-insert per asset (§N.3); new `build_runs`/`build_run_assets`; refreshed `asset_provenance_receipts`/`asset_freshness`; `asset_throughput` re-lit; downstream stale marks cleared; ordinary conversation/reading rows unaffected |
| Failure containment | orchestrator-owned savepoint per sub-step; a failed asset rolls back its own sub-step, leaves the run `failed` and the chart not-ready (fail-closed); no manual status change or SQL repair; stop after two identical failures and produce a root-cause packet |
| Backup | fresh production backup and restore proof per the prior campaigns' pattern before dispatch |
| Excluded | retired `ka_gochara_sweep` and protected L3 history (Gochara v1 snapshot); no `ka_*` producer-specific ad hoc run |
| Concurrent writers | must be confirmed zero: no active `build_runs`, no L3 lease, no unreleased `bg_transit` repair |

## 5. Post-build verification (Decision 2 item 7)

1. terminal `build_runs.state = completed`; 2. `getChartReadinessMap` state `ready`; 3. every active
per-chart asset terminally `lit` or explicitly permitted non-building; 4. no `bo_*`/`ka_*`/`ph_*`/`mi_*`
asset `stale`/`error` from the rebuilt generation; 5. resolver returns no unresolved asset for the
consumed set, `ga_strength` receipt proven under the active spec; 6. managed MCP `prashna_ask` no
longer returns `CHART_RECOMPUTE_REQUIRED`; 7. no protected L3 history or retired asset rebuilt.

## 6. L3 coordination request (ready to post — NOT posted)

Text intended for `CAMPAIGN_COORDINATION.md` §6 LOG on `origin/campaign-coordination`, as
`PA-REQ` under interlock I-2. It has not been pushed because pushing is not yet required.

> PA-REQ (Pūrṇa Anveṣaṇa → L3 Kāla, 2026-09-29). Pūrṇa acceptance needs the canonical chart
> `482012f1-…` at a coherent Ready state via one full frozen-orchestrator rebuild. Requested from
> L3 owner: (1) merge or explicitly withdraw #2731, #2715, #2717, #2695 and state which L3 source is
> intended for the rebuild revision; (2) confirm 1086 (`ga_strength` contributor spec) lands BEFORE
> that rebuild; (3) confirm the standing no-build order and the WP10 resonance-rebuild sequencing, and
> whether L3 wants its own rebuild folded into the same run; (4) report no active/pending build or
> data mutation on this chart and release the `bg_transit` FK blocker; (5) name the point at which
> Pūrṇa may claim the exclusive rebuild lease. Pūrṇa will not build, rebuild or backfill any `ka_*`
> producer itself. Until answered, Pūrṇa records `BLOCKED_ON_L3_RECEIPT(ka_dasha_kala, ka_gochara)`.

## 7. Decision status

- Decision 1 (provider lane): transferred to Owner-Surrogate Ruling OSR-003. No human credential
  operation is authorized; the campaign must use or build on an existing protected system-owned
  identity and record a terminal external dependency only if that is proven impossible.
- Decision 2 (rebuild): Owner-Surrogate Rulings OSR-002, OSR-004, and OSR-005 govern. The single
  protected full rebuild is conditionally authorized once the enumerated technical prerequisites
  pass. The conductor must post the L3 request, resolve integration through repository evidence,
  and use protected auditable automation rather than wait for a manual super-admin click.
- Near-miss ratification: transferred to OSR-001; no Native response is required.
