#!/usr/bin/env bash
# Compatibility entrypoint. There is one watchdog provisioning contract; keep
# this historical filename from recreating a second, header-authenticated job.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/provision_watchdog_scheduler.sh" "$@"
