#!/bin/bash
# kynotify.sh — owner-facing notification for KĀLA-YANTRA v3 (relaunch plan §4a.3, §6 Messaging).
#
#   kynotify.sh "<message>" [--level info|decision|hard_stop]
#
# 1. Submits a macOS notification unless KY_NOTIFY_DRY=1. The message reaches osascript ONLY as an
#    argument (`on run argv`), never as script text, so nothing in it is ever evaluated.
# 2. THEN appends ONE line to $KY_RUN/JOURNAL_COCKPIT.md (a single printf append):
#        - <UTC ISO> [<level>] <message> [notify=submitted|failed|dry]
#    The timestamp is taken AFTER the submission attempt and the line always ENDS with the result that was
#    really observed — whatever the message itself says. Every line-breaking character in the message (CR, LF,
#    VT, FF, FS/GS/RS, NEL, U+2028, U+2029) is flattened to a space, so a message can never forge a second
#    journal line. The veto handler reads this line: one whose message begins `<SD id>:` and that ends
#    `[notify=submitted]` is its evidence that the owner's window was opened, and when.
#
# Stdout: EXACTLY one line — `notify=submitted`, `notify=failed` or `notify=dry`. A caller records the
#       submission as made only when that line is exactly `notify=submitted` (delivery is never evidence
#       that the owner read it). Diagnostics go to stderr.
# Exit: 0 once the journal line is written (a failed or dry notification is not fatal: read stdout);
#       3 if the journal append failed (the notification was still attempted); 64 on usage errors.
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

flatten() {   # bytewise, so that the multi-byte separators are matched whatever the caller's locale is
  local LC_ALL=C s="$1" c
  for c in $'\r' $'\n' $'\v' $'\f' $'\x1c' $'\x1d' $'\x1e' $'\xc2\x85' $'\xe2\x80\xa8' $'\xe2\x80\xa9'; do
    s="${s//"$c"/ }"
  done
  FLAT="$s"
}
flatten "$msg"; msg="$FLAT"
[ -n "${msg// /}" ] || usage

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
    echo "kynotify: notification submission failed (rc=$rc)" >&2
  fi
fi

ts="$(/bin/date -u +%Y-%m-%dT%H:%M:%SZ)"
journal=ok
if ! { printf -- '- %s [%s] %s [notify=%s]\n' "$ts" "$level" "$msg" "$notify" >> "$JOURNAL"; } 2>/dev/null; then
  journal=failed
  echo "kynotify: cannot append to $JOURNAL" >&2
fi

echo "notify=$notify"
[ "$journal" = ok ] || exit 3
exit 0
