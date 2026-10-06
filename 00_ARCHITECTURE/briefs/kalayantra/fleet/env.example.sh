# KĀLA-YANTRA — the operator's one-time environment for the launch shell (charter §7).
# Copy to ~/.config/kalayantra/env.sh (chmod 600), fill the two credentials, and `source` it before `kalayantra_fleet.sh up`.
# Nothing in this file is read by any agent; the supervisor passes the two URLs into ONE lane's process environment,
# only during a dispatch-armed cycle. Agents never print, log or commit them (surrogate charter H8).

export KY_ROOT=/Users/Dev/kalayantra

# Production build dispatch (J-2, J-3, J-4, K9-4): the data_plane_builder connection. Leave empty to defer dispatch items.
export KY_BUILDER_DATABASE_URL=''

# Small-test TEARDOWN only (needs DELETE; data_plane_builder cannot). Leave empty → ADHIKĀRIN applies D-TEARDOWN's
# alternative (unsealed candidate rows retained; no teardown).
export KY_OWNER_DATABASE_URL=''

# Fleet sizing and pacing (charter §3.3, §11)
export KY_WORKERS=4                 # initial worker count; SŪTRADHĀRA adjusts via $KY_ROOT/run/KY_WORKERS (ceiling 6)
export KY_MAX_CYCLES_PER_DAY=400
export KY_QUOTA_BACKOFF_S=1800

# Models (defaults shown)
export KY_MODEL_WORKER=gpt-6.1-sol;      export KY_EFFORT_WORKER=high
export KY_MODEL_SUTRADHARA=gpt-6.1-sol;  export KY_EFFORT_SUTRADHARA=high
export KY_MODEL_ADHIKARIN=gpt-6-astra;   export KY_EFFORT_ADHIKARIN=xhigh
export KY_MODEL_PARIKSAKA=gpt-6-astra;   export KY_EFFORT_PARIKSAKA=xhigh

# Swiss ephemeris (preflight downloads + sha256-verifies the three .se1 files here)
export SE_EPHE_PATH=$KY_ROOT/ephe
