# Memorystore (Redis) IaC

Provisions the shared `amjis-cache` Redis instance consumed by the
`amjis-web` + `amjis-mcp` Cloud Run services for retrieval-bundle / planner
/ Vertex-embedding caching.

## Files

- `main.tf` — resource definition (1 GB BASIC tier, asia-south1, LRU eviction).
- `backend.tf` — GCS remote state.
- `apply.sh` — idempotent plan/apply/destroy wrapper.

## Operator runbook (post-merge to main)

```bash
cd infra/memorystore
./apply.sh plan
./apply.sh apply
```

The apply prints `REDIS_HOST` + `REDIS_PORT` — set them as `vars` on the
GitHub repo (Settings → Secrets and variables → Actions → Variables) so the
next deploy picks them up via `.github/workflows/deploy.yml`:

```yaml
env_vars: |
  REDIS_HOST=${{ vars.REDIS_HOST }}
  REDIS_PORT=${{ vars.REDIS_PORT }}
```

## Rollback

`./apply.sh destroy` — application gracefully falls back to compute-on-miss
(see `platform/src/lib/cache/redis_client.ts`); no functional regression,
just the latency floor returns to pre-Memorystore.
