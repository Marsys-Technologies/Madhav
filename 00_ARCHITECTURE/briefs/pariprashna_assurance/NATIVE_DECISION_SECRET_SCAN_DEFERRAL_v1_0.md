---
canonical_id: NATIVE_DECISION_SECRET_SCAN_DEFERRAL
version: 1.0
status: RECORDED
date: 2026-08-30
authority: native, given directly in conversation during the Paripraśna v3.0 final closeout session
changelog:
  - version: 1.0
    date: 2026-08-30
    change: Initial record of the native's deferral ruling and the mechanism chosen to implement it.
---

# Native decision — secret-scan remediation deferred, deadline extended

## What expired

`platform/scripts/governance/secret_scan.sh`'s required CI check began failing repo-wide on
2026-08-30 because all 33 rows in `platform/scripts/governance/secret_scan_inherited.txt`
(six owner lanes: `DVA-ESCALATION-SEC-002` ×17, `B-SECRET-REDACT` ×9, `DVA-ESCALATION-SEC-004`
×3, `DVA-ESCALATION-SEC-003` ×2, `DVA-ESCALATION-SEC-005` ×1, `DVA-ESCALATION-SEC-006` ×1)
shared the same remediation deadline, `2026-08-29`, and expired simultaneously at midnight.
Confirmed independently to reproduce on a pristine `origin/main` checkout — not caused by any
in-flight PR. Full detail: `PARIPRASHNA_V3_FINAL_CLOSE_REPORT_v1_0.md` and PR #1667's own
comment thread.

## The native's ruling (verbatim in substance)

> I'm not interested in secret scan, secrets, passwords, managing them. This is an internal
> product and development stage — just ignore those, don't put effort into those. Do the
> needful.

Given directly in this session, with full authorization to decide the implementation mechanism
with due diligence.

## Mechanism chosen, and why

**Extended all 33 expiry dates from `2026-08-29` to `2027-08-29`.** Did **not** remove the
Secret Scan check from the branch ruleset's required-checks list.

Alternatives considered and rejected:

- **Remove the check from the ruleset (make it non-required).** Rejected: this permanently
  disables detection of *new* credential leaks, not just the effort the native declined to
  spend on the 33 pre-existing inherited findings. The native's instruction was about not
  investing remediation effort on what's already flagged, not about turning the detector off.
  Silently weakening a gate this way is exactly what CLAUDE.md §N.8 (Earned-Signal Principle)
  warns against — a status that no longer measures the thing it claims to.
- **Admin/bypass merge.** Structurally unavailable — the ruleset's `bypass_actors` is empty and
  `current_user_can_bypass` reads `never` for this repository.

Extending the deadline is the register's own designed mechanism (the file format has a
per-row `expiry` field precisely so remediation timelines can be revisited) and keeps the check
**green and fully functional**: any new or grown finding still fails the build immediately,
unchanged. Nothing is silenced. The owner lanes (`DVA-ESCALATION-SEC-002` through `-006`,
`B-SECRET-REDACT`) and their underlying findings are untouched — this record does not close,
resolve, or dismiss any of them, it only defers their remediation clock by twelve months per
the native's stated priority.

## Scope note

This decision covers only the *deadline* on the 33 already-registered findings. It does not:

- Authorize committing any new credential material anywhere in the repository.
- Change the CI-side gitleaks posture (CI does not run gitleaks at all; only `secret_scan.sh`'s
  own pattern pass runs in CI — this was true before and after this change).
- Apply to any future finding — a new leak fails the build the moment it's introduced, exactly
  as before.

## Next horizon

2027-08-29. Twelve months was this session's own judgment call, not a native-specified figure —
flagged for the native to shorten or lengthen if twelve months doesn't match their intent.
