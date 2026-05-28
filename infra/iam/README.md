# infra/iam — Per-service runtime service accounts

MARSYS-JIS Platform Modernization Wave 4 unit `4.edge_and_infra_hygiene`.

## What this codifies

Four least-privilege runtime SAs, one per Cloud Run service / build pipeline:

| Service account                          | Role on                                                                   | Justification                                  |
|------------------------------------------|---------------------------------------------------------------------------|------------------------------------------------|
| `amjis-web-runtime`                      | Cloud SQL client, Secret Manager accessor, Cloud Run invoker on `amjis-mcp` + `amjis-sidecar`, Vertex AI user, GCS object viewer on chart-documents | The web frontend; calls MCP + sidecar + DB.    |
| `amjis-sidecar-runtime`                  | Cloud SQL client, Secret Manager accessor                                 | Python sidecar; no MCP or Vertex calls.        |
| `amjis-mcp-runtime`                      | Cloud SQL client, Secret Manager accessor, Cloud Run invoker on `amjis-web`, GCS object viewer | MCP server; calls platform routes + reads corpus. |
| `amjis-builder-runtime`                  | Artifact Registry writer, Cloud Run admin on the 3 services above        | The deploy pipeline (used by WIF in GH Actions). |

The build SA (`amjis-builder-runtime`) is the **deploy identity**; the three runtime SAs are
attached to the corresponding Cloud Run revisions via `--service-account=`. This replaces the
prior pattern where every service ran under the project default compute SA (`<project_number>-compute@developer.gserviceaccount.com`).

## Files

- `main.tf` — SA resources + IAM role grants + role binding to enable WIF to impersonate the builder SA.
- `backend.tf` — GCS-backed terraform remote state.
- `apply.sh` — idempotent plan/apply wrapper.

## Wired into deploy.yml

The Cloud Run `deploy-cloudrun@v2` step pins each service's `service_account` to its runtime SA;
see the `# ── 4.edge_and_infra_hygiene ──` fence block in `.github/workflows/deploy.yml`.

## MCP ingress IAM gate

The MCP service is flipped from `--allow-unauthenticated` → `--no-allow-unauthenticated` in both
`platform-mcp/cloudbuild.yaml` (legacy / image-build-only path) and the deploy.yml MCP deploy step.
The web runtime SA holds `run.invoker` on `amjis-mcp`, so the web service can call MCP using a
service-account identity token (already wired in `platform-mcp/src/client.ts`, hardened in this
commit to use `google-auth-library` for token acquisition + caching).
