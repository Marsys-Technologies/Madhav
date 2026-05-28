# infra/secrets — Secret Manager naming normalization + version pinning

MARSYS-JIS Platform Modernization Wave 4 unit `4.edge_and_infra_hygiene`.

## What this codifies

Audit + normalization plan for Secret Manager secrets referenced by Cloud Run services.
Codified, not applied — operator-side rotation per `secret_inventory.yaml`.

## Files

- `secret_inventory.yaml` — current vs canonical secret names + intended access SAs.
- `rotation_policy.md` — cadence (90d for high-sensitivity API keys, 180d for DB password, ad-hoc on incident).

## Hygiene rule (codified)

- No `:latest` pin on production deploys for high-sensitivity secrets (`*_API_KEY`, `firebase-admin-credentials`).
  - **Current state**: deploy.yml references `:latest` for all secrets (legacy).
  - **Target state**: pin a specific `projects/.../secrets/X/versions/N` reference; rotate via PR.
  - **Smoke check**: `edge_security_smoke.sh` greps deploy.yml for `:latest` and emits a WARN
    count (non-fatal — operator-tracked rotation). All entries listed in `secret_inventory.yaml`.

## Apply path

Operator runs the rotation procedure documented in `rotation_policy.md` outside this worktree.
The codified state here is the audit; rotation is a runtime activity.
