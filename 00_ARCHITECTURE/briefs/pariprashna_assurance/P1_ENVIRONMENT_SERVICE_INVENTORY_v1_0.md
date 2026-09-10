# P1 environment, service, and provenance inventory v1.0

## Current P1 control plane

| Item | Classification | Evidence |
| --- | --- | --- |
| Service | ACCEPTED_PRIMARY_EVIDENCE | `com.marsys.pariprashna-assurance-control` is launchd-running, loopback `127.0.0.1:8787`, with `--p0b-only --p1-enabled`. |
| Release | ACCEPTED_PRIMARY_EVIDENCE | Read-only retry release `ca4fd54ef8e1…-retry1`; its source marker and manifest name protected merge `ca4fd54ef8e142713b100c60cf718ea6c46b12bb`. The earlier `872df060…` and `58e9c797…` releases remain historical deployment evidence only. |
| Runtime | ACCEPTED_PRIMARY_EVIDENCE | Runtime is private (`0700`); database, logs, and credential-file metadata are private (`0600`). Credential contents are not inspected or versioned. |
| Integrity | ACCEPTED_PRIMARY_EVIDENCE | `/api/integrity` returned `ok:true`; projector and monitor were healthy after the P1 start presence. |
| P1 execution | ACCEPTED_PRIMARY_EVIDENCE | Session `codex-p1-takeover-872df060` has the single append-only P1-F-004 duration correction (`259200` seconds). The P1 phase lifecycle is COMPLETE after independent verification and integrator acceptance; the session record remains historical RUNNING while presence is COMPLETED/STALE. |
| Negative boundary | ACCEPTED_PRIMARY_EVIDENCE | Valid `lead-p0b` P1 start attempt was rejected `STREAM_FORBIDDEN`; no P1 work was accepted from P0B. |

## Branches and worktrees

- Original isolated P1 takeover worktree: `/Users/Dev/.codex/worktrees/7561/Madhav`,
  branch `codex/pariprashna-assurance-p1`. Its identity-enablement merge
  `872df060…` is historical provenance, not the current deployed code.
- Current closure worktree: `/Users/Dev/.codex/worktrees/7561/Madhav-p1-closure`,
  branch `codex/pariprashna-assurance-p1-closure`. The current deployed release
  is attested only to protected merge `ca4fd54ef8e142713b100c60cf718ea6c46b12bb`.
- Historical self-paused worktree and P0B worktree are separate and untouched.

## Process and liveness boundaries

- Historical `pulse.sh` under `/Users/Dev/pariprashna_night` has no verified
  P1 attribution: **UNKNOWN_REQUIRES_RESOLUTION**; it was not touched.
- Historical heartbeat records and `verify_heartbeat_provenance.sh` are
  **DO_NOT_RELY**. The latter misclassified 13 legitimate prior-timer rows;
  no historic timer demonstrates current P1 health.
- P1 liveness is only the current Option-B `/api/presence` record. It is
  COMPLETED but STALE after the P1 close; it does not make any historical
  process current, reopen P1, or authorize P2 execution.
