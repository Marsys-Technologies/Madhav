# infra/iam — Per-service runtime service accounts

MARSYS-JIS Platform Modernization Wave 4 unit `4.edge_and_infra_hygiene`.

## What this codifies

Four least-privilege runtime SAs, one per Cloud Run service / build pipeline:

| Service account                          | Role on                                                                   | Justification                                  |
|------------------------------------------|---------------------------------------------------------------------------|------------------------------------------------|
| `amjis-web-runtime`                      | Cloud SQL client, Secret Manager accessor, Cloud Run invoker on `amjis-mcp` + `amjis-sidecar`, Cloud Run viewer on `amjis-web`, Vertex AI user, GCS object viewer on chart-documents | The web frontend; calls MCP + sidecar + DB and observes its own immutable release provenance. |
| `amjis-sidecar-runtime`                  | Cloud SQL client, Secret Manager accessor                                 | Python sidecar; no MCP or Vertex calls.        |
| `amjis-mcp-runtime`                      | Cloud SQL client, Secret Manager accessor, Cloud Run invoker on `amjis-web`, GCS object viewer | MCP server; calls platform routes + reads corpus. |
| `amjis-builder-runtime`                  | Artifact Registry writer only                                             | Retained dormant identity; no WIF, Cloud Run mutation, or runtime actAs authority. |

The live deploy identity is `github-actions@madhav-astrology.iam.gserviceaccount.com`; this root
binds it only to two exact `Marsys-Technologies/Madhav` OIDC subjects: protected `main` for routine
deploy jobs, and the protected `data-plane-production-cutover` environment for its one-time
bootstrap job. GitHub uses an environment subject in place of the ref subject when a job enters an
environment, so both narrow bindings are required. Its read-only Logging Viewer grant lets the
cutover verifier bind a Cloud SQL restore operation to its exact backup through Admin Activity
audit evidence; Cloud SQL's operation response omits that source-backup field. The three runtime SAs are attached to the
corresponding Cloud Run revisions via `--service-account=`. The legacy builder is deliberately
unable to deploy or act as a runtime. This replaces the prior pattern where every service ran under
the project default compute SA (`<project_number>-compute@developer.gserviceaccount.com`).

## Files

- `main.tf` — SA resources + IAM role grants + exact protected-main and protected-environment WIF bindings for the live deploy SA.
- `backend.tf` — GCS-backed terraform remote state.
- `apply.sh` — idempotent plan/apply wrapper.

## Wired into deploy.yml

The Cloud Run `deploy-cloudrun@v2` step pins each service's `service_account` to its runtime SA;
see the `# ── 4.edge_and_infra_hygiene ──` fence block in `.github/workflows/deploy.yml`.

## MCP ingress application gate

The public MCP front door deliberately uses Cloud Run `--allow-unauthenticated` so external MCP
clients can reach the application OAuth/Bearer-token layer. Cloud Run IAM is therefore not the
MCP ingress security boundary. Internal Pūrṇa calls additionally require the shared internal token
and a Google OIDC token pinned to the expected caller service account and audience; candidate
deployment probes exercise that combined path before traffic promotion. The web runtime's
`run.invoker` binding remains useful for authenticated service-to-service calls but is not claimed
as the public MCP gate.
