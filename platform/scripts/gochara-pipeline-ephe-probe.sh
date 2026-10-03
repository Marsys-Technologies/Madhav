#!/usr/bin/env bash
# gochara-pipeline-ephe-probe.sh — Pravāha C42: READ-ONLY probe of the pinned Swiss ephemeris
# corpus inside the pipeline job's CURRENT image.
#
#   usage: gochara-pipeline-ephe-probe.sh JOB REGION [--project P] [--run]
#
# Default mode is --print: print the exact command sequence and exit. --run executes it.
#
# WHY THIS SHAPE (do not "improve" it into a job override): `gcloud run jobs execute` supports
# --args and --update-env-vars but NO --command override (verified against the installed gcloud,
# GA and beta), and brahma-build-pipeline-job's ENTRYPOINT is `python -m pipeline.orchestrator.
# main` — an args-only override cannot make it run sha256sum. So the probe never touches the job:
# it resolves the job's CURRENT image (gcloud run jobs describe, read-only) and digests the .se1
# files by running THAT image locally with an entrypoint override (docker run --entrypoint
# sha256sum) — the exact bytes Cloud Run would start. The pins are READ from
# platform/python-sidecar/tests/l3/gochara/conftest.py (SE1_CHECKSUMS), never retyped here.
#
# WHAT THIS PROVES: the three .se1 files in the deployed image hash to the pinned digests, and the
# image's SE_EPHE_PATH env value. WHAT IT DOES NOT PROVE: anything about a running execution's
# filesystem (there are no volume mounts; the image is the whole story), and nothing about any
# database. No credentials are printed; nothing is written outside the local docker daemon.
#
# Exit codes: 0 digests match · 1 mismatch / missing file / probe failure · 2 usage/preflight refusal.
set -euo pipefail

JOB="${1:-}"; REGION="${2:-}"
[ $# -ge 2 ] && shift 2
PROJECT="madhav-astrology"
MODE="print"
while [ $# -gt 0 ]; do
  case "$1" in
    --project) PROJECT="${2:?--project needs a project id}"; shift ;;
    --run) MODE="run" ;;
    --print) MODE="print" ;;
    *) echo "usage: $0 JOB REGION [--project P] [--run]" >&2; exit 2 ;;
  esac
  shift
done
[ -n "$JOB" ] && [ -n "$REGION" ] || { echo "usage: $0 JOB REGION [--project P] [--run]" >&2; exit 2; }

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CONFTEST="$REPO_ROOT/platform/python-sidecar/tests/l3/gochara/conftest.py"
EPHE_DIR="/app/ephe"
FILES=(sepl_18.se1 semo_18.se1 seas_18.se1)

read_pins() { # "name sha256" lines, parsed (never executed) from conftest.py's SE1_CHECKSUMS
  python3 - "$CONFTEST" <<'PY'
import ast, sys
tree = ast.parse(open(sys.argv[1], encoding="utf-8").read())
for node in ast.walk(tree):
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "SE1_CHECKSUMS" for t in node.targets):
        for name, sha in sorted(ast.literal_eval(node.value).items()):
            print(name, sha)
        break
else:
    sys.exit("SE1_CHECKSUMS not found in " + sys.argv[1])
PY
}

DESCRIBE=(gcloud run jobs describe "$JOB" --region="$REGION" --project="$PROJECT"
          "--format=value(template.template.containers[0].image)")
SHA_CMD=(docker run --rm --entrypoint sha256sum)
ENV_CMD=(docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}')

if [ "$MODE" = "print" ]; then
  paths=(); for f in "${FILES[@]}"; do paths+=("$EPHE_DIR/$f"); done
  echo "# 1. resolve the job's CURRENT image (read-only):"
  echo "${DESCRIBE[*]}"
  echo "# 2. digest the three pinned .se1 files inside THAT image (local, entrypoint override):"
  echo "${SHA_CMD[*]} <IMAGE> -- ${paths[*]}"
  echo "# 3. echo the image's SE_EPHE_PATH:"
  echo "${ENV_CMD[*]} <IMAGE>   # grep '^SE_EPHE_PATH='"
  echo "# 4. compare the three digests with the pins READ from:"
  echo "#    $CONFTEST (SE1_CHECKSUMS) — exit 1 on any mismatch or missing file"
  exit 0
fi

for tool in gcloud docker python3; do
  command -v "$tool" > /dev/null || { echo "REFUSAL: $tool not on PATH" >&2; exit 2; }
done
[ -f "$CONFTEST" ] || { echo "REFUSAL: conftest not found: $CONFTEST" >&2; exit 2; }

IMAGE="$("${DESCRIBE[@]}")" || { echo "REFUSAL: could not describe $JOB" >&2; exit 2; }
[ -n "$IMAGE" ] || { echo "REFUSAL: $JOB carries no image" >&2; exit 2; }
echo "image: $IMAGE"

paths=(); for f in "${FILES[@]}"; do paths+=("$EPHE_DIR/$f"); done
DIGESTS="$("${SHA_CMD[@]}" "$IMAGE" -- "${paths[@]}")" || { echo "REFUSAL: digest run failed" >&2; exit 2; }
echo "$DIGESTS"
"${ENV_CMD[@]}" "$IMAGE" | grep '^SE_EPHE_PATH=' || echo "SE_EPHE_PATH not set in the image env"

rc=0
while read -r name pin; do
  got="$(echo "$DIGESTS" | awk -v p="$EPHE_DIR/$name" '$2 == p {print $1}')"
  if [ -z "$got" ]; then
    echo "MISSING: $name not in the digest output" >&2; rc=1
  elif [ "$got" != "$pin" ]; then
    echo "MISMATCH: $name $got != pinned $pin" >&2; rc=1
  else
    echo "OK: $name matches the pin"
  fi
done < <(read_pins)
[ "$rc" -eq 0 ] && echo "RESULT: all three .se1 digests match the conftest pins"
exit "$rc"
