# infra/edge — External HTTPS LB + Cloud CDN + Cloud Armor

MARSYS-JIS Platform Modernization Wave 4 unit `4.edge_and_infra_hygiene`.

## What this codifies

A regional external HTTPS load balancer fronting Cloud Run (`amjis-web`) with:

- **Cloud CDN** enabled on the backend, configured for path-based caching:
  - `_next/static/*` → long-lived immutable (max-age 1y, cache-key includes content hash already).
  - Chart-document GCS reads (`/api/charts/.../document`) → 5-min TTL with revalidation.
  - All other paths bypass CDN (passes through to Cloud Run).
- **Cloud Armor** WAF + rate-limit policy attached to the backend:
  - WAF rule: OWASP-style XSS preset block (`evaluatePreconfiguredExpr('xss-v33-stable')`).
  - Rate-limit rule: 60 RPS/IP throttle on `/api/*` (per-IP fair-use).

## Files

- `main.tf` — provider + LB + backend + CDN + URL map + forwarding rule.
- `cloud_armor.tf` — security policy with WAF + rate-limit rules; attached to backend service.
- `cloud_armor_rules.json` — declarative rule catalogue (used by the smoke script + audit).
- `backend.tf` — GCS-backed terraform remote state.
- `apply.sh` — idempotent plan/apply wrapper (operator-side; NOT executed from this worktree).

## Apply discipline

IaC only. `apply` runs on `main` once the unit's commits land — never from a worktree. The smoke
script `platform/scripts/governance/edge_security_smoke.sh` verifies the codified files are
present + the rule shapes are correct; it does NOT call gcloud.

## Acceptance pointers

1. `infra/edge/` exists with LB + CDN + Armor terraform — this directory.
2. `cloud_armor_rules.json` contains ≥ 1 WAF rule + ≥ 1 rate-limit rule — see file.
3. CDN policy attached to backend service in `main.tf` — `google_compute_backend_service.amjis_web_cdn.enable_cdn = true`.

## Out of scope (deferred)

- Static IP allocation + DNS record creation (operator-managed via console; outputs surface the LB IP).
- mTLS or VPC Service Controls — future hardening.
- Edge functions / CDN signed URLs — future.
