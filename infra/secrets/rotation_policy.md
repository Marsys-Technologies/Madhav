# Secret rotation policy

Wave 4 4.edge_and_infra_hygiene — codified policy. Operator executes outside this worktree.

## Cadence

| Secret class                       | Rotation cadence | Trigger                                         |
|------------------------------------|------------------|-------------------------------------------------|
| Provider API keys (`*_API_KEY`)    | 90 days          | Calendar + on incident                          |
| DB password (`amjis-db-password`)  | 180 days         | Calendar + on suspected leak / member departure |
| Firebase admin credentials         | 365 days         | On membership change in IAM                     |
| `mcp-internal-token`               | 180 days         | Calendar + on MCP-related security event        |

## Procedure (per secret)

1. Mint a new version of the secret in Secret Manager:
   `gcloud secrets versions add <secret-name> --data-file=- < new-value.txt`
2. Update deploy.yml / platform-mcp/cloudbuild.yaml to reference the new version pin
   (`projects/<proj>/secrets/<name>/versions/N`, not `:latest`).
3. Open PR → wait for CI green → squash merge.
4. Verify new revision is healthy (log watch 10 min).
5. Disable the prior version in Secret Manager:
   `gcloud secrets versions disable <secret-name> --version=PRIOR_N`
6. After 7 days with no incident, destroy the prior version.

## Naming convention

- Secret names: lowercase-with-hyphens (`anthropic-api-key`, `mcp-internal-token`).
- Env var names: UPPER_SNAKE_CASE (`ANTHROPIC_API_KEY`).
- Legacy uppercase secret names listed in `secret_inventory.yaml` with `rename_to:` targets.
- Renames are non-breaking: create new secret with canonical name, dual-write for one rotation
  cycle, then retire the old name.
