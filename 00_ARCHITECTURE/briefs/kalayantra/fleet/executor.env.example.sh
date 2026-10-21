# KĀLA-YANTRA — EXECUTOR environment (the ONLY place a production credential lives). Copy to ~/.config/kalayantra/executor.env,
# chmod 600, fill, and `source` it ONLY in the shell that runs fleet/executor.sh. Never source it where the fleet or Codex runs.
export KY_ROOT=/Users/Dev/kalayantra
export KY_BUILDER_DATABASE_URL=''    # the builder connection — production build operations (small tests, measuring build, flip, layer rebuild); launching small tests/measuring also requires gcloud; the verifier uses its own remote runtime principal. Empty → those items wait on capability_missing; everything else proceeds.
export KY_LAYER_VERIFIER_DATABASE_URL=''  # a separate verifier_principal login; layer_verify and layer_verify_dryrun only (K9-23). Never the builder or owner connection. Empty → those two kinds wait on capability_missing.
export KY_OWNER_DATABASE_URL=''      # the owner-level connection — small-test TEARDOWN only. Empty → the small tests wait (there is no retention alternative).
export SE_EPHE_PATH=$KY_ROOT/ephe

# Whole-layer verifier only; executor passes this alone to layer_verify.
export KY_LAYER_VERIFIER_DATABASE_URL=''  # separately provisioned verifier_principal; empty means capability_missing
