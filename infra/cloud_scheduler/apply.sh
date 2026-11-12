#!/usr/bin/env bash
# Compatibility entrypoint only; never initialize the retired Terraform backend.
printf '%s\n' 'The default build-reaper module is retired; no Terraform or cloud operation is supported here.' 'For current watchdog provisioning, see platform/scripts/provision_watchdog_scheduler.sh; use its separately reviewed operator procedure.' >&2
exit 2
