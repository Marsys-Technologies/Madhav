---
stream: postdeploy-c
session: c1-docker-check-and-defer
tier: 2
decision: DEFER
timestamp: 2026-06-05
---

# Stream C — Docker Unavailable — Deferred

Docker is not available on the current conductor runner. Stream C (migration squash test)
requires Docker to spin a clean Postgres container for schema diff validation.

## Resolution

Stream C defers cleanly per brief §3. The deferral tag `postdeploy-c-deferred-docker`
marks this stream as wave-complete.

Re-run when Docker is available:
```bash
docker ps >/dev/null 2>&1 && bash stream_c_resume.sh
```

## No changes to source tree were made.
