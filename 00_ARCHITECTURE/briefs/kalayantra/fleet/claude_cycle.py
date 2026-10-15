#!/usr/bin/env python3
"""Run one KĀLA-YANTRA lane cycle with Claude Code in print mode (the Codex `exec` equivalent).

argv: claude_bin worktree model last_file ky_root ; the cycle prompt arrives on stdin.
Writes the final answer to last_file (the supervisor reads its last line for IDLE-OK) and streams every event to stdout
(the supervisor's cycle log). Exit code: Claude's, or 3 when the stream ended without a result.
"""
import json, os, subprocess, sys

claude_bin, worktree, model, last_file, ky_root = sys.argv[1:6]
prompt = sys.stdin.read()
cmd = [claude_bin, "-p", "--permission-mode", "bypassPermissions", "--model", model,
       "--setting-sources", "local", "--strict-mcp-config", "--no-session-persistence",
       "--output-format", "stream-json", "--verbose", "--add-dir", ky_root]
proc = subprocess.Popen(cmd, cwd=worktree, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
proc.stdin.write(prompt); proc.stdin.close()
result = None; is_error = False
for line in proc.stdout:
    sys.stdout.write(line); sys.stdout.flush()
    try: ev = json.loads(line)
    except ValueError: continue
    if ev.get("type") == "result":
        result = ev.get("result") or ""; is_error = bool(ev.get("is_error"))
        if is_error and not result: result = json.dumps({k: ev.get(k) for k in ("subtype", "error")})
rc = proc.wait()
if result is None:
    print("ERROR: Claude stream ended without a result event", flush=True); rc = rc or 3
else:
    with open(last_file, "w") as f: f.write(result.rstrip() + "\n")
    if is_error:
        print(f"ERROR: Claude reported an error result: {result[:300]}", flush=True); rc = rc or 1
sys.exit(rc)
