#!/bin/bash
# Fake `claude` reporting the version the plan refuses (P-2: 2.1.239 rejected claude-opus-5-5).
# If it is ever launched it leaves a marker, so a test can prove it was not.
if [ "$1" = "--version" ]; then
  echo "2.1.239 (Claude Code)"
  exit 0
fi
echo "launched" > "${TMPDIR:-/dev/null}/fake_old_was_launched.txt"
exit 0
