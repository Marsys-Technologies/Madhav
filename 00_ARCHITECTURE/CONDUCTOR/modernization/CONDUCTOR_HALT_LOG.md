# CONDUCTOR_HALT_LOG — Platform Modernization (open halts)

> Append a section per `halt_queue` event. A halt stops the WHOLE queue until resolved.
> Read at every re-kick; resolved halts moved to `## Resolved halts` (kept for audit).

## Open halts
- _None._

## Pre-declared blocker (operational input, not a halt)
- `jh_oracle_pinned` — RED. Unit 1.2 (engine→JH parity, gate G1) is INELIGIBLE until
  `platform/python-sidecar/natal_engine/fixtures/jh_oracle.json` is dropped by the native:
  - JH version/build to treat as authority,
  - ayanamsha (e.g. Lahiri/Chitrapaksha 23°37′58″ per FORENSIC),
  - reference outputs for native 1984-02-05 captured once from that JH build.
  Until then the Conductor skips 1.2 and runs everything else.

## Resolved halts
- _None._
