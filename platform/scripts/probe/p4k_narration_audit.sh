#!/usr/bin/env bash
# p4k_narration_audit.sh — THE ONE COMMAND the CONDUCTOR/VERIFIER runs post-flip to
# execute the P4-K narration audit against the live default surface.
#
# P4-K is a FILLER(build)/post-flip(run) lane (PLAN.yaml, charter §10.2/§10.5): this
# harness is built and self-tested tonight but is NOT executed against any live
# surface as part of the build. Running THIS script for real is the post-flip act.
#
# Usage (post-flip, against the live default surface):
#   ./p4k_narration_audit.sh --service-url https://amjis-web-qm256lasva-el.a.run.app
#
# Usage (against a tagged 0%-traffic revision, e.g. pre-flip verification):
#   ./p4k_narration_audit.sh --service-url https://<tagged-revision-url>
#
# Usage (offline, no network — proves the harness itself is sound; this is what
# tonight's build actually ran):
#   ./p4k_narration_audit.sh --self-test
#
# Exit code: 0 iff the analyzer found zero fail-severity deterministic findings.
# Judgment items are always printed and never affect the exit code — see
# p4k_narration_analyzer.ts's own header for why.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../.."   # repo root

if [[ "${1:-}" == "--self-test" ]]; then
  echo "[p4k_narration_audit] --self-test: offline structural + fixture self-check, no network." >&2
  npx tsx platform/scripts/probe/p4k_sequence_driver.ts --self-test
  npx tsx platform/scripts/probe/p4k_narration_analyzer.ts --self-test
  exit $?
fi

if [[ "${1:-}" != "--service-url" || -z "${2:-}" ]]; then
  echo "Usage: $0 --service-url <url> | --self-test" >&2
  exit 2
fi
SERVICE_URL="$2"

echo "[p4k_narration_audit] driving six-view sequence against ${SERVICE_URL} …" >&2
MANIFEST_PATH="$(npx tsx platform/scripts/probe/p4k_sequence_driver.ts --service-url "${SERVICE_URL}")"
echo "[p4k_narration_audit] manifest: ${MANIFEST_PATH}" >&2

echo "[p4k_narration_audit] analyzing …" >&2
exec npx tsx platform/scripts/probe/p4k_narration_analyzer.ts --manifest "${MANIFEST_PATH}"
