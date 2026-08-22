#!/usr/bin/env bash
# Agent-free external health record (charter §11.4). No agent writes here.
LOG="/Users/Dev/pariprashna_night/logs/pulse.log"; REPO="/Users/Dev/Vibe-Coding/Apps/Madhav"; PROD_URL=""
while true; do
  {
    echo "=== $(date -u +%FT%TZ) ==="
    git -C "$REPO" --no-optional-locks fetch origin --quiet 2>/dev/null       && echo "origin/main: $(git -C "$REPO" --no-optional-locks rev-parse --short origin/main)"       || echo "origin/main: FETCH FAILED"
    gh run list --repo "$(git -C "$REPO" config --get remote.origin.url | sed -E 's#(git@github.com:|https://github.com/)##; s#\.git$##')" -L 5       --json name,status,conclusion,createdAt       --template '{{range .}}{{.name}} {{.status}} {{.conclusion}} {{.createdAt}}{{"\n"}}{{end}}' 2>/dev/null       || echo "gh runs: UNAVAILABLE"
    if [[ -n "$PROD_URL" ]]; then
      echo "prod: HTTP $(curl -s -o /dev/null -m 20 -w '%{http_code}' "$PROD_URL" || echo FAIL)"
    fi
    echo "disk: $(df -h / | awk 'NR==2{print $4" free"}')"
    echo ""
  } >> "$LOG"
  sleep 1800
done
