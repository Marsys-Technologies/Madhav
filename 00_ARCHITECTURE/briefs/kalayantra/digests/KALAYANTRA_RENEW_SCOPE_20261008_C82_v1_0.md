---
artifact: KALAYANTRA_RENEW_SCOPE_20261008_C82
version: "1.0"
status: SOURCE_SCOPE_REVIEW_REQUIRED
produced_on: 2026-10-08
---

# Existing claim-recovery scope — documented renewal identity

KYD100 consolidates original K6 report M20261007T230233-d96d into B-CLAIM-RECOVERY. The documented `ky renew <ID>` currently fails argument parsing; flag-only renewal works. This source scope selects optional item-ID support and retains flag-only compatibility.

Original K6 owns implementation in `platform/scripts/governance/pravaha_tracker/cli.py` and disposable parser/ownership tests in `platform/scripts/governance/pravaha_tracker/tests/test_pravaha.py`. A supplied ID must match the owner's current claim; mismatched/unknown identity refuses before any event or claim-file change. It never selects a peer's claim. Existing ownership, checkpoint recovery, concurrent retry, dependency/HOLD, join derivation and type-refusal requirements remain mandatory and independently testable.

The real J-0b recovery reproduced null checkpoint metadata at acquisition, followed by original-owner normal renewal restoring it. Preserve those original events and reproduce the defect in disposable source tests. CLI parser success alone proves neither checkpoint recovery nor correct join status. Meaningful equality-guard and parser-removal mutants must fail their own oracles.

Only this existing item's brief changes; all 188 identities, the other 187 items, dependencies, ownership, steps, detectors and non-item model fields remain unchanged. This document registers scope, not implementation, runtime adoption, acceptance, READY or completion. No installed controller, fleet script, peer claim or foreign campaign is changed. Exact source review, required current CI including applicable database checks, protected merge and separately authorized measured local adoption precede runtime-use acceptance.
