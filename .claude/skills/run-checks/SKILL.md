---
name: run-checks
description: Run the full Madhav quality gate — ESLint, TypeScript, and test suite — and report results. Use before raising a PR.
---

Run these commands in sequence from `platform/`:

```bash
# 1. Lint
npm run lint 2>&1 | tail -20

# 2. Type check
npx tsc --noEmit --skipLibCheck 2>&1 | grep -c 'error TS' || echo "0 type errors"

# 3. Unit tests
npm run test 2>&1 | tail -30

# 4. Python tests (if orchestrator changed)
# Note: test files live under platform/scripts/ AND platform/python-sidecar/ — scope broadly
cd .. && python -m pytest platform/ -x -q --ignore=platform/node_modules --ignore=platform/.next 2>&1 | tail -20
```

Report format:
```
ESLint:     PASS / N warnings / N errors
TypeScript: PASS / N errors
Tests:      N passed, N failed
Python:     N passed, N failed (or SKIPPED if no orchestrator changes)
```

If any gate fails, stop and report. Do not raise a PR with failing gates.
