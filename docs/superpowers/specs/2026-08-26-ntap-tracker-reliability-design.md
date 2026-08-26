---
title: NTAP Tracker Reliability and Plan-Adaptation Design
date: 2026-08-26
status: APPROVED_IN_CONVERSATION
surface: /admin/nirmana-elevation
extends: docs/superpowers/specs/2026-08-25-nirmana-elevation-campaign-spine-design.md
---

# NTAP Tracker Reliability and Plan-Adaptation Design

## Outcome

The authenticated Nirmāṇa Elevation Tracker becomes the one operational dashboard for the NTAP program. It must show the accepted program baseline, the governed vertical campaign spine, live build state, source health, release alignment, and any proposed plan adaptation. It must never convert an absent baseline, a quiet program, or a failed monitor into apparent progress.

## Truth model

The dashboard has four distinct truths, displayed separately:

1. **Accepted plan** is the current frozen campaign definition and its selected bilingual label catalogue.
2. **Execution truth** is `build_runs`, `build_run_assets`, `build_substep_progress`, and `asset_throughput` for the canonical Nirmāṇa chart.
3. **Acceptance truth** is append-only campaign evidence. It alone advances a stage or asset lifecycle milestone.
4. **Observation truth** is an append-only monitor record that says when the live registry, execution tables, campaign evidence, and deployed release were last compared.

Historical JSON/JSONL ledgers remain evidence-only. They are not a source for initializing progress, stage position, or completion.

## Controlled initialization

The first successful monitor run may create a **reconciling proposal** from the live registry only when no current definition exists. It must not silently freeze it or create stage-transition receipts.

An authenticated super-admin explicitly accepts that exact proposed digest through the existing evidence boundary. The acceptance transaction must:

- re-read the registry under the existing definition guards;
- create and freeze the immutable definition only when the candidate digest still matches;
- create a complete versioned label catalogue from authoritative registry labels, with every missing human label rendered as `Not yet catalogued` rather than invented;
- append a single initialization receipt describing the source snapshot and digests; and
- leave campaign-stage progress at `unknown` until independently accepted stage receipts exist.

This is intentionally an initialization of program identity, not a backfill of historical campaign progress. `BOOTSTRAP`, `T0_CENSUS`, `PLAN_FROZEN`, `DENOMINATOR_FROZEN`, `F0_FOUNDATION`, and L0–L5 only advance from their typed earned receipts.

## Continuous monitoring and divergence detection

A Cloud Scheduler-triggered, service-authenticated monitor runs every five minutes. It performs read-only comparisons and appends one observation result. It may create a reconciling proposal when the program has no definition, but it must not freeze, supersede, advance a stage, accept a label catalogue, dispatch a build, or mutate build tables.

Each observation stores canonical digests for:

- the ordered registry identity and DAG;
- mutable registry contracts;
- the current frozen definition;
- the selected label catalogue;
- live execution/run state; and
- main/deployed release reconciliation.

The monitor classifies an outcome as one of:

- `in_sync` — current plan identity matches the live registry and all sources were read;
- `baseline_missing` — no accepted frozen definition exists;
- `plan_adaptation_required` — asset membership, layer, or dependency identity changed;
- `evidence_refresh_required` — a mutable registry contract changed and asset analysis must be re-accepted;
- `label_refresh_required` — a selected label is incomplete or a governed catalogue no longer covers the frozen manifest;
- `release_attention` — main and deployed release differ or provenance is unavailable; or
- `source_unavailable` — an authoritative source could not be read.

Only `plan_adaptation_required` is a plan change. The dashboard must name the affected assets and show the current and candidate definition digests. A super-admin must explicitly use the existing transactional supersession path to adopt a changed plan; the monitor never makes that choice.

## Freshness and stillness

“Fresh” means a successful authoritative read and an observation timestamp inside the five-minute cadence plus a ten-minute grace period. It does not mean assets are actively building. A program with no active run can be fresh and explicitly quiet. A missing or late monitor is `stale`, never green.

The page continues client refresh while open. The monitor status is included in every snapshot, so a healthy browser cannot mask an unobserved program. Source failures retain the last good observation only as context and make the current conclusion degraded.

## Dashboard behavior

The existing campaign spine remains the primary view and retains the exact stage vocabulary:

`BOOTSTRAP → T0_CENSUS → PLAN_FROZEN → DENOMINATOR_FROZEN → F0_FOUNDATION → L0 → L1 → L2 → L3 → L4 → L5 → CLOSING → COMPLETE`.

L0–L5 remain vertical sequential stages. Waves remain vertical within a layer; only DAG peers remain horizontal. Every asset continues to show canonical ID, Sanskrit name, English name, plain-language description, lifecycle bar, blockers, dependencies, and unlocks.

The executive strip gains a compact **Program synchronization** measure and a visible **Plan adaptation** notice. It says whether the dashboard is in sync, quiet, stale, awaiting baseline acceptance, or awaiting plan adoption. Detailed source digests and observation history remain in the audit drawer.

## Security and safety

- The dashboard and snapshot remain super-admin only.
- The monitor endpoint accepts only the existing scheduler secret and requires no user credentials.
- Scheduler requests cannot write execution or acceptance state.
- Initialization and plan adoption remain explicit audited super-admin actions, idempotent, and transactionally guarded.
- No raw historical ledger import, manual percentages, or progress override is permitted.
- The change does not alter the frozen build orchestrator or trigger campaign work.

## Acceptance criteria

1. A missing baseline appears as `Baseline awaiting acceptance`, never stale or 0% complete.
2. A successful monitor observation appears with its timestamp and becomes stale after the cadence grace window.
3. A registry identity/DAG change produces `Plan adaptation required`, names affected assets, and withholds a new denominator until explicit adoption.
4. A mutable contract change produces `Evidence refresh required`, not a false plan change.
5. Scheduler authentication failures and source errors become degraded notices without accepting progress or writing a supersession.
6. The existing vertical spine and bilingual collapsible asset experience stay intact.
7. Tests cover first baseline proposal, stale monitor, every divergence category, scheduler authentication, idempotency, and the UI’s executive notices.
