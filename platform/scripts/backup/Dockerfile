# Dockerfile for the G1-E logical-export Cloud Run Job runner.
#
# Minimal image: Debian + the postgresql-client package (pg_dump/pg_restore
# matching the target Cloud SQL major version) + this lane's three scripts.
# No application code, no Next.js build — this job does exactly one thing.
#
# Build context is platform/scripts/backup/ itself (see
# provision_logical_export_scheduler.sh's `gcloud builds submit
# "$(dirname ...)"` call), so COPY paths below are relative to this
# directory, not the repo root.

FROM debian:bookworm-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends postgresql-client ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app/platform/scripts/backup
COPY export_irreplaceable_tables.sh restore_irreplaceable_tables.sh irreplaceable_table_sets.sh ./
RUN chmod +x export_irreplaceable_tables.sh restore_irreplaceable_tables.sh

ENTRYPOINT ["/app/platform/scripts/backup/export_irreplaceable_tables.sh"]
