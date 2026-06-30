#!/bin/bash
# Pre-commit credential detection for .env.local
# Add to .git/hooks/pre-commit or wire via husky

ENV_FILE="platform/.env.local"
if [ -f "$ENV_FILE" ]; then
  if grep -qE '(sk-ant-api|sk-proj-|-----BEGIN PRIVATE KEY-----|AIza[0-9A-Za-z_-]{35}|password.*=.*[A-Za-z0-9]{20,})' "$ENV_FILE" 2>/dev/null; then
    echo "ERROR: platform/.env.local appears to contain live credentials."
    echo "Use GCP Secret Manager or op run -- instead of storing secrets in .env.local"
    echo "If this is intentional (local dev only), add: # SKIP-CREDENTIAL-CHECK"
    exit 1
  fi
fi
