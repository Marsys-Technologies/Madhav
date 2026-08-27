---
title: NTAP Tracker Operational Repair Design
date: 2026-08-27
status: APPROVED_IN_CONVERSATION
surface: /admin/nirmana-elevation
extends: docs/superpowers/specs/2026-08-26-ntap-tracker-reliability-design.md
---

# NTAP Tracker Operational Repair Design

## Outcome

The Nirmana Elevation Tracker becomes decision-ready without overstating what is known. It must distinguish a healthy data connection from an accepted program baseline and from earned execution progress. It must let a super-admin safely complete the missing baseline step once a fresh scheduler observation exists.

## Product repair

The executive strip must not display `0 / 128` as elevation progress when the accepted campaign spine is unavailable. In that condition it instead says that the accepted denominator and earned execution position are unavailable, alongside the exact remediation state.

The vertical spine retains the approved vocabulary: BOOTSTRAP, T0, PLAN FROZEN, DENOMINATOR FROZEN, F0, L0 through L5, CLOSING, and COMPLETE. Human-readable names are primary; implementation identifiers remain secondary audit details.

Each expanded layer presents sequential waves vertically. Within a wave, DAG peers can remain side-by-side, but each asset card must show a stable plan-facing asset reference when one exists, a human name, plain-language description, a real accessible completion bar, one next action, and one concise blocker. Missing Sanskrit or plan-facing names are shown once as unavailable; the UI never repeats placeholder text three times.

## Operational completion path

1. A protected-main Terraform scheduler apply provisions the already-reviewed five-minute monitor job and its IAM binding.
2. A secret-aware operator configures the existing scheduler secret in the request header through the approved secret-injection mechanism. The value is never read, logged, checked into source, or shown in this dashboard.
3. The scheduler emits a fresh `baseline_missing` observation.
4. A super-admin sees a guarded baseline proposal panel, reviews the current candidate digest/count and accepts that exact proposal. The acceptance remains transactional, idempotent, and audit-recorded; it creates identity/labels only, not stage progress.
5. Subsequent observations make the page current. In the absence of earned campaign receipts it says "Execution not yet evidenced", not 0% complete.

## Safety rules

- No historical ledger import, manual percentage, synthetic Sanskrit translation, or made-up stage receipt.
- The monitor remains read-only with respect to campaign acceptance and execution.
- Only a current, fresh `baseline_missing` observation can enable the baseline action.
- Baseline acceptance freezes a current candidate and labels; it does not begin or resume campaign work.
- Scheduler applies happen only via the protected-main infrastructure workflow. Secret configuration stays outside Terraform and source control.
- A release is complete only after the deployed page shows a fresh monitor status and the truth-safe UX; accepting a baseline additionally requires explicit super-admin action.

## Acceptance criteria

1. No missing-spine snapshot can visually imply zero earned progress or a usable frozen denominator.
2. Every asset card exposes an accessible progress bar and concise, non-repetitive identity copy.
3. Stage and layer display labels use the approved plan language while preserving exact IDs in audit detail.
4. A fresh `baseline_missing` snapshot presents a safeguarded, test-covered acceptance action; unavailable/stale/changed candidates cannot be accepted.
5. The production scheduler route receives a fresh observation without exposing its secret.
6. The live tracker reports either current synchronized state or an explicit actionable degraded state; it never silently goes stale.
