#!/bin/bash
# Fake `claude` that ignores SIGTERM, with a child that does the same: only SIGKILL of the whole process
# group ends it within a test's time. Both give up by themselves after 120 s, so that a supervisor whose
# kill path is broken cannot leave them behind for ever. Works with /bin/bash 3.2.
if [ "$1" = "--version" ]; then
  echo "2.1.296 (Claude Code)"
  exit 0
fi
trap '' TERM
out="${TMPDIR:?TMPDIR is not set}"
echo '{"type":"system","subtype":"init","session_id":"5e55105e-0000-4000-8000-0000000000aa","tools":[]}'
( trap '' TERM; n=0; while [ $n -lt 120 ]; do sleep 1; n=$((n + 1)); done ) &
echo $! > "$out/fake_child_pid.txt"
echo $$ > "$out/fake_pid.txt"
n=0
while [ $n -lt 120 ]; do sleep 1; n=$((n + 1)); done
