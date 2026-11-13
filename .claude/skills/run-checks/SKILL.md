---
name: run-checks
description: Run the local Madhav pre-PR checks for the Web platform and, for orchestrator changes, the Python suite. Report each result and check hosted CI separately.
---

Before arming a PR, run the source-evidence battery from the repository root.
Use the existing Python environment with
`platform/python-sidecar/requirements-ci.txt` installed. Set `BASE_REF` to the
accepted comparison base covering the complete change. Use owned approved
`.noindex` scratch for `TMPDIR` and pytest.

```bash
: "${BASE_REF:?Set the accepted complete-change base}"
: "${TMPDIR:?Set owned approved .noindex scratch}"
classification=$(python3 platform/scripts/governance/ci_changes.py --event pull_request --base "$BASE_REF" --head HEAD) || classification=docs_only=false
if [ "$classification" = docs_only=true ]; then
  echo 'Source evidence battery is NOT APPLICABLE for proven unpinned docs only'
else
  python3 platform/scripts/governance/ci_changes.py --run-source-evidence
fi
```

A failure or timeout stops PR arming. Report a proven documentation-only skip as
NOT APPLICABLE. The battery validates 102 served-SQL citations, ten committed
density cases and their existing negative controls. Unavailable or malformed
comparison inputs select the battery. The full orchestrator and protected
combination suites retain their existing selection and checks.

Run this block in Bash from `platform/`. Set `run_orchestrator_tests=1` before running it if the orchestrator changed. It stops at the first failed check.

```bash
(
  set -o pipefail

  tail_check() (
    lines=$1
    shift
    "$@" 2>&1 | tail -n "$lines"
    statuses=("${PIPESTATUS[@]}")
    if (( statuses[0] != 0 )); then
      exit "${statuses[0]}"
    fi
    exit "${statuses[1]}"
  )

  # 1. Lint
  tail_check 20 npm run lint || exit $?

  # 2. Type check
  tsc_status=0
  tsc_output=$(npx tsc --noEmit --skipLibCheck 2>&1) || tsc_status=$?
  count_status=0
  printf '%s\n' "$tsc_output" | awk '/error TS/ { count++ } END { print count+0 " TypeScript diagnostic lines" }' || count_status=$?
  if (( tsc_status != 0 )); then
    printf 'TypeScript failed (exit %s).\n%s\n' "$tsc_status" "$tsc_output" >&2 || :
    exit "$tsc_status"
  fi
  if (( count_status != 0 )); then
    exit "$count_status"
  fi

  # 3. Web unit tests
  tail_check 30 npm run test || exit $?

  # 4. Python tests, when orchestrator code changed
  # Tests live under both platform/scripts/ and platform/python-sidecar/.
  if [[ ${run_orchestrator_tests:-0} == 1 ]]; then
    cd .. || exit $?
    tail_check 20 python -m pytest platform/ -x -q --ignore=platform/node_modules --ignore=platform/.next || exit $?
  fi
)
```

Report each check as passed, failed, or skipped. Include ESLint warning and error counts, TypeScript diagnostic count and exit status on failure, and the test totals when available. A TypeScript invocation can fail without printing a diagnostic. Resolve any failure before raising a PR.

The local TypeScript command checks the program in `platform/tsconfig.json`, including test sources. Check the hosted results for the exact PR head and applicable merge-group checks separately.

- [Ganga Quality Gate](../../../.github/workflows/ci.yml) includes generated artifacts, MCP and evaluation lint, MCP typechecking, governance and event-selected database jobs. Its Web TypeScript job filters diagnostics to source paths.
- [Build Check (PR only)](../../../.github/workflows/deploy.yml) runs no-push image builds for selected PR changes.
- [Chat V2 — Workstream CI](../../../.github/workflows/chat-v2-ci.yml) adds separate component, integration and Chromium stages for matching PRs.
