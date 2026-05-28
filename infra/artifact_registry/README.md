# infra/artifact_registry — AR cleanup policy

MARSYS-JIS Platform Modernization Wave 4 unit `4.edge_and_infra_hygiene`.

## What this codifies

`cleanup_policy.json` — declarative Artifact Registry cleanup policy for the `amjis` repository
in `asia-south1`. Three rules:

1. Keep the 10 most-recent tagged versions of `amjis-web`, `amjis-sidecar`, `amjis-mcp`.
2. Delete untagged images older than 7 days.
3. Delete `sha-` / `pr-` tagged images older than 90 days.

## Migration off legacy gcr.io

Acceptance item 6 + the brief's "secret + registry hygiene" line:

- `.github/workflows/deploy.yml` image refs point at `asia-south1-docker.pkg.dev/madhav-astrology/amjis/...` for all three services.
- `platform-mcp/cloudbuild.yaml` retained for image-build path only (trigger is GH Actions now); MCP image migration to AR happens in the GH Actions deploy-mcp job in deploy.yml.

## Apply

```
gcloud artifacts repositories set-cleanup-policies amjis \
  --location=asia-south1 \
  --policy=infra/artifact_registry/cleanup_policy.json \
  --no-dry-run
```

Operator-only. The smoke script verifies the JSON shape (≥ 1 KEEP, ≥ 1 DELETE rule).
