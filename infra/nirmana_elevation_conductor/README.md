# Nirmāṇa non-browser conductor

This isolated Terraform root provisions two new workload identities only:

- `amjis-nirmana-conductor`: invokes the fixed conductor callback.
- `amjis-nirmana-verifier`: invokes the same callback only for independent readiness verification.

Neither identity receives Cloud SQL, Secret Manager, Artifact Registry, Cloud Run Admin, IAM administration, or deployment access. The application route verifies each OIDC token's exact audience and subject, so Cloud Run invocation alone is insufficient to select an action.

Use `./apply.sh plan <saved-plan>` to produce a reviewed plan. `./apply.sh apply <saved-plan>` refuses static credentials and personal accounts; it requires a reviewed `madhav-astrology` service-account identity and a recorded production approval. GitHub Actions intentionally does not apply this module.
