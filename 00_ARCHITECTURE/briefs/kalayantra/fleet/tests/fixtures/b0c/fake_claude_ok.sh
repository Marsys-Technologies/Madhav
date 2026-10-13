#!/bin/bash
# Fake `claude` for kyboot tests — never the real program. Works with /bin/bash 3.2.
# `--version` reports the pinned minimum. Otherwise it records what it was given (argv, environment names,
# working directory, process group, stdin) and what the supervisor had already written when it started (the
# action records, the locks and their owner records under $KY_RUN) under $TMPDIR, obeys the FAKE_* lines of its
# prompt (stdin), and prints a small stream-json transcript: a system/init event carrying a session_id, then a
# final result event. FAKE_RESULT_JSON:<json> makes it leave $JOB_SCRATCH/result.json (the job's own report);
# FAKE_RESULT_SYMLINK:<path> makes that a symbolic link instead; without either it leaves no result.
if [ "$1" = "--version" ]; then
  echo "2.1.296 (Claude Code)"
  exit 0
fi
out="${TMPDIR:?TMPDIR is not set}"
printf '%s\n' "$@" > "$out/fake_argv.txt"
env | LC_ALL=C sort > "$out/fake_env.txt"
pwd -P > "$out/fake_cwd.txt"
ps -o pgid= -p $$ | tr -d ' ' > "$out/fake_pgid.txt"
if [ -n "$KY_RUN" ]; then
  cat "$KY_RUN"/actions/*.json > "$out/fake_actions_at_launch.txt" 2>/dev/null
  ls "$KY_RUN/locks" > "$out/fake_locks_at_launch.txt" 2>/dev/null
  cat "$KY_RUN"/locks/*/owner.json > "$out/fake_owner_at_launch.txt" 2>/dev/null
fi
: > "$out/fake_stdin.txt"
code=0
session='"session_id":"0f1e2d3c-4b5a-4978-8695-a4b3c2d1e0f9",'
nap=""
leftover=""
no_result=""
while IFS= read -r line || [ -n "$line" ]; do
  printf '%s\n' "$line" >> "$out/fake_stdin.txt"
  case "$line" in
    FAKE_RESULT_JSON:*) printf '%s\n' "${line#FAKE_RESULT_JSON:}" > "${JOB_SCRATCH:?JOB_SCRATCH is not set}/result.json" ;;
    FAKE_RESULT_SYMLINK:*) ln -s "${line#FAKE_RESULT_SYMLINK:}" "${JOB_SCRATCH:?JOB_SCRATCH is not set}/result.json" ;;
    FAKE_EXIT:*) code="${line#FAKE_EXIT:}" ;;
    FAKE_NO_SESSION) session="" ;;
    FAKE_NO_RESULT_EVENT) no_result=1 ;;
    FAKE_SLEEP:*) nap="${line#FAKE_SLEEP:}" ;;
    FAKE_LEFTOVER:*) leftover="${line#FAKE_LEFTOVER:}" ;;
  esac
done
echo "{\"type\":\"system\",\"subtype\":\"init\",${session}\"model\":\"claude-opus-5-5\",\"tools\":[]}"
echo "this line is not JSON and is skipped"
echo "{\"type\":\"assistant\",${session}\"message\":{\"role\":\"assistant\",\"content\":[{\"type\":\"text\",\"text\":\"working\"}]}}"
echo "fake stderr line" >&2
if [ -n "$leftover" ]; then
  sleep "$leftover" &
  echo $! > "$out/fake_leftover_pid.txt"
fi
if [ -n "$nap" ]; then
  sleep "$nap"
fi
if [ -z "$no_result" ]; then
  echo "{\"type\":\"result\",\"subtype\":\"success\",\"is_error\":false,\"num_turns\":3,${session}\"usage\":{\"input_tokens\":31000,\"output_tokens\":120},\"result\":\"done\"}"
fi
exit "$code"
