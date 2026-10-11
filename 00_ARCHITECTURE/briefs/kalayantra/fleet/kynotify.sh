#!/bin/bash
# kynotify.sh — owner-facing notification for KĀLA-YANTRA v3 (relaunch plan §4a.3, §6 Messaging).
#
#   kynotify.sh "<message>" [--level info|decision|hard_stop]
#
# 1. Appends ONE line `- <UTC ISO> [<level>] <message>` to $KY_RUN/JOURNAL_COCKPIT.md (a single
#    printf append; newlines in the message are flattened to spaces).
# 2. Submits a macOS notification unless KY_NOTIFY_DRY=1. The message reaches osascript ONLY as an
#    argument (`on run argv`), never as script text, so nothing in it is ever evaluated.
#
# Exit: 0 once the journal line is written (a failed notification is recorded as a second
#       `[notify_failed]` line and reported on stdout, never fatal); 3 if the journal append failed
#       (the notification is still attempted); 64 on usage errors.
# Stdout (for the caller's record — the plan stores the SUBMISSION result; delivery is never
#       evidence that the owner read it):  kynotify: journal=ok|failed notify=submitted|failed|dry
set -euo pipefail

KY_ROOT="${KY_ROOT:-/Users/Dev/kalayantra}"
KY_RUN="${KY_RUN:-$KY_ROOT/run}"
OSASCRIPT="${KY_OSASCRIPT:-/usr/bin/osascript}"
JOURNAL="$KY_RUN/JOURNAL_COCKPIT.md"

usage() { echo 'usage: kynotify.sh "<message>" [--level info|decision|hard_stop]' >&2; exit 64; }

msg=""; have_msg=0; level="info"
while [ "$#" -gt 0 ]; do
  case "$1" in
    --level) [ "$#" -ge 2 ] || usage; level="$2"; shift 2 ;;
    --level=*) level="${1#--level=}"; shift ;;
    *) [ "$have_msg" -eq 0 ] || usage; msg="$1"; have_msg=1; shift ;;
  esac
done
[ "$have_msg" -eq 1 ] || usage
case "$level" in info|decision|hard_stop) ;; *) usage ;; esac

msg="${msg//$'\r'/ }"
msg="${msg//$'\n'/ }"
[ -n "${msg// /}" ] || usage

ts="$(/bin/date -u +%Y-%m-%dT%H:%M:%SZ)"
journal=ok
if ! { printf -- '- %s [%s] %s\n' "$ts" "$level" "$msg" >> "$JOURNAL"; } 2>/dev/null; then
  journal=failed
  echo "kynotify: cannot append to $JOURNAL" >&2
fi

notify=dry
if [ "${KY_NOTIFY_DRY:-0}" != "1" ]; then
  rc=0
  "$OSASCRIPT" -e 'on run argv' \
               -e 'display notification (item 1 of argv) with title "KĀLA-YANTRA v3"' \
               -e 'end run' -- "$msg" >/dev/null 2>&1 || rc=$?
  if [ "$rc" -eq 0 ]; then
    notify=submitted
  else
    notify=failed
    if [ "$journal" = ok ]; then
      { printf -- '- %s [notify_failed] notification submission failed (rc=%s) for the preceding [%s] entry\n' \
          "$ts" "$rc" "$level" >> "$JOURNAL"; } 2>/dev/null || true
    fi
  fi
fi

echo "kynotify: journal=$journal notify=$notify"
[ "$journal" = ok ] || exit 3
exit 0
