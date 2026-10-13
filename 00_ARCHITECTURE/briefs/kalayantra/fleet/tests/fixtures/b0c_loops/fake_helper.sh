#!/bin/bash
# Test double for the later-deliverable helpers kyversion.sh and kygate.sh (B-0c loop tests).
# Records its argv in <script>.calls and exits with the integer in <script>.rc (default 0).
set -u
printf '%s\n' "$*" >> "$0.calls"
if [ -f "$0.rc" ]; then exit "$(cat "$0.rc")"; fi
exit 0
