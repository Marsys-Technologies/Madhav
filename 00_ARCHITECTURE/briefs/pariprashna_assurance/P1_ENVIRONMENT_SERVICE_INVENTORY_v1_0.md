# P1 environment, service, and provenance inventory v1.0

## Current P1 control plane

| Item | Classification | Evidence |
| --- | --- | --- |
| Service | ACCEPTED_PRIMARY_EVIDENCE | `com.marsys.pariprashna-assurance-control` is launchd-running, loopback `127.0.0.1:8787`, with `--p0b-only --p1-enabled`. |
| Release | ACCEPTED_PRIMARY_EVIDENCE | Read-only release `872df060152a…`; source marker and manifest name the same protected merge SHA. |
| Runtime | ACCEPTED_PRIMARY_EVIDENCE | Runtime is private (`0700`); database, logs, and credential-file metadata are private (`0600`). Credential contents are not inspected or versioned. |
| Integrity | ACCEPTED_PRIMARY_EVIDENCE | `/api/integrity` returned `ok:true`; projector and monitor were healthy after the P1 start presence. |
| P1 execution | OPEN_BLOCKER_FOR_P2 | Session `codex-p1-takeover-872df060` has a textual P1-only scope ceiling and no cost claim, but its operational duration `ceiling` was omitted. P1-F-004 must be append-only corrected, merged, and deployed before closure. |
| Negative boundary | ACCEPTED_PRIMARY_EVIDENCE | Valid `lead-p0b` P1 start attempt was rejected `STREAM_FORBIDDEN`; no P1 work was accepted from P0B. |

## Branches and worktrees

- Current isolated P1 worktree: `/Users/Dev/.codex/worktrees/7561/Madhav`,
  branch `codex/pariprashna-assurance-p1`, clean before P1 documentation.
- The P1 branch head `9ed1b107…` differs from the protected squash/queue merge
  SHA `872df060…`. This is a normal source-provenance distinction, not a
  deployed-code contradiction: the release is attested to the latter. It must
  remain explicit in later PR evidence.
- Historical self-paused worktree and P0B worktree are separate and untouched.

## Process and liveness boundaries

- Historical `pulse.sh` under `/Users/Dev/pariprashna_night` has no verified
  P1 attribution: **UNKNOWN_REQUIRES_RESOLUTION**; it was not touched.
- Historical heartbeat records and `verify_heartbeat_provenance.sh` are
  **DO_NOT_RELY**. The latter misclassified 13 legitimate prior-timer rows;
  no historic timer demonstrates current P1 health.
- P1 liveness is only the current Option-B `/api/presence` record. It became
  HEALTHY after the active lead-p1 presence was recorded.
