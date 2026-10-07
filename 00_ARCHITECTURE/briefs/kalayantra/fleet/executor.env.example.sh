# KĀLA-YANTRA — EXECUTOR environment (the ONLY place a production credential lives). Copy to ~/.config/kalayantra/executor.env,
# chmod 600, fill, and `source` it ONLY in the shell that runs fleet/executor.sh. Never source it where the fleet or Codex runs.
export KY_ROOT=/Users/Dev/kalayantra
export KY_BUILDER_DATABASE_URL=''    # the builder connection — production build operations (small tests, measuring build, verification job, flip, layer rebuild). Empty → those items wait on capability_missing; everything else proceeds.
export KY_OWNER_DATABASE_URL=''      # the owner-level connection — small-test TEARDOWN only. Empty → the small tests wait (there is no retention alternative).
export SE_EPHE_PATH=$KY_ROOT/ephe
