#!/bin/bash
# Fake `codex` for kyboot tests — never the real program. Works with /bin/bash 3.2.
# `--version` prints "codex-cli 0.162.0-alpha.17.2". Otherwise it records what it was given (argv, environment
# names, working directory, process group, stdin) under $TMPDIR, obeys the FAKE_* lines of its prompt (stdin), and
# prints a small `codex exec --json` transcript: thread.started carrying a thread_id, turn.started, one
# agent_message item, turn.completed. Like the real program it writes the last agent message to the -o file.
# FAKE_RESULT_JSON:<json> makes it leave $JOB_SCRATCH/result.json; FAKE_FINAL_MESSAGE:<text> is the last message
# (default "done"); FAKE_EXIT:<n>, FAKE_SLEEP:<s>, FAKE_NO_THREAD (no thread.started), FAKE_TURN_FAILED;
# FAKE_TOUCH:<path> appends a line to <path> (a job that changes what it must leave alone);
# FAKE_WRITE:<path>|<text> replaces <path> with <text> and a newline, creating its folder.
if [ "$1" = "--version" ]; then
  echo "codex-cli 0.162.0-alpha.17.2"
  exit 0
fi
out="${TMPDIR:?TMPDIR is not set}"
printf '%s\n' "$@" > "$out/fake_argv.txt"
env | LC_ALL=C sort > "$out/fake_env.txt"
pwd -P > "$out/fake_cwd.txt"
ps -o pgid= -p $$ | tr -d ' ' > "$out/fake_pgid.txt"
final=""
previous=""
for arg in "$@"; do
  if [ "$previous" = "-o" ]; then
    final="$arg"
  fi
  previous="$arg"
done
: > "$out/fake_stdin.txt"
code=0
thread="0199c0de-0000-7000-8000-00000000c0de"
nap=""
message="done"
failed=""
while IFS= read -r line || [ -n "$line" ]; do
  printf '%s\n' "$line" >> "$out/fake_stdin.txt"
  case "$line" in
    FAKE_RESULT_JSON:*) printf '%s\n' "${line#FAKE_RESULT_JSON:}" > "${JOB_SCRATCH:?JOB_SCRATCH is not set}/result.json" ;;
    FAKE_FINAL_MESSAGE:*) message="${line#FAKE_FINAL_MESSAGE:}" ;;
    FAKE_EXIT:*) code="${line#FAKE_EXIT:}" ;;
    FAKE_NO_THREAD) thread="" ;;
    FAKE_SLEEP:*) nap="${line#FAKE_SLEEP:}" ;;
    FAKE_TURN_FAILED) failed=1 ;;
    FAKE_TOUCH:*) printf '# changed by a job\n' >> "${line#FAKE_TOUCH:}" ;;
    FAKE_WRITE:*) spec="${line#FAKE_WRITE:}"; mkdir -p "$(dirname "${spec%%|*}")"; printf '%s\n' "${spec#*|}" > "${spec%%|*}" ;;
  esac
done
if [ -n "$thread" ]; then
  echo "{\"type\":\"thread.started\",\"thread_id\":\"$thread\"}"
fi
echo '{"type":"turn.started"}'
echo "this line is not JSON and is skipped"
echo "fake stderr line" >&2
if [ -n "$nap" ]; then
  sleep "$nap"
fi
echo '{"type":"item.completed","item":{"id":"item_1","type":"agent_message","text":"working"}}'
if [ -n "$final" ]; then
  printf '%s' "$message" > "$final"
fi
if [ -n "$failed" ]; then
  echo '{"type":"turn.failed","error":{"message":"stream disconnected"}}'
else
  echo '{"type":"turn.completed","usage":{"input_tokens":21000,"cached_input_tokens":0,"output_tokens":80}}'
fi
exit "$code"
