#!/bin/bash
# Run this as a GitHub admin to enforce CI on main branch pushes.
# Branch protection was applied live on 2026-06-30 via gh CLI.
# This script documents the exact configuration applied and can be re-run if
# protection is ever accidentally removed.
REPO="$(git remote get-url origin | sed 's/.*github.com\///' | sed 's/\.git$//')"
echo "Configuring branch protection for $REPO main..."
gh api "repos/$REPO/branches/main/protection" --method PUT \
  --field 'required_status_checks[strict]=true' \
  --field 'required_status_checks[contexts][]=CI — Ganga Quality Gate / typecheck' \
  --field 'required_status_checks[contexts][]=CI — Ganga Quality Gate / unit-tests' \
  --field 'required_status_checks[contexts][]=CI — Ganga Quality Gate / secret-scan' \
  --field 'required_status_checks[contexts][]=CI — Ganga Quality Gate / governance-gates' \
  --field 'enforce_admins=true' \
  --field 'required_pull_request_reviews=null' \
  --field 'restrictions=null'
echo "Done."
