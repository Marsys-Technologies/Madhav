"""Steward watcher: tails the event log and prints one line per event the steward must act on.

Run under Claude Code's Monitor so each printed line wakes the steward session. Prints: messages to the
steward; items parked / blocked / in review / failed; decision requests; stream items marked done.
"""
import json, os, sys, time
PATH = os.environ.get("PRAVAHA_EVENTS", "/Users/Dev/pravaha/run/EVENTS.jsonl")
STATE = os.path.join(os.path.dirname(PATH), "steward_watch.offset")
f = open(PATH, encoding="utf-8"); ino = os.fstat(f.fileno()).st_ino
try:  # resume where the last watcher stopped, so nothing written between re-arms is missed
    s_ino, s_off = map(int, open(STATE).read().split())
    f.seek(s_off if s_ino == ino and s_off <= os.fstat(f.fileno()).st_size else 0, 0 if s_ino == ino else 2)
except (OSError, ValueError):
    f.seek(0, 2)
def save():
    try:
        open(STATE, "w").write(f"{ino} {f.tell()}")
    except OSError:
        pass
while True:
    line = f.readline()
    if not line:
        time.sleep(2)
        try:
            if os.stat(PATH).st_ino != ino:
                f = open(PATH, encoding="utf-8"); ino = os.fstat(f.fileno()).st_ino
        except OSError:
            pass
        continue
    save()
    try:
        e = json.loads(line)
    except ValueError:
        continue
    k, a = e.get("kind"), e.get("actor", "")
    d = (e.get("detail") or "").replace("\n", " ")[:300]
    if k == "message" and e.get("to") == "steward":
        print(f"MSG {e.get('msg_id')} from {a} [{e.get('ref','')}]: {d}", flush=True)
    elif k == "item" and e.get("state") in ("parked", "blocked", "review", "failed") and a.startswith("stream-"):
        print(f"ITEM {e['item']} -> {e['state']} by {a}: {d}", flush=True)
    elif k == "item" and e.get("state") == "done" and a.startswith("stream-") and not e.get("step"):
        print(f"DONE {e['item']} by {a}: {(e.get('evidence') or '')[:200]}", flush=True)
    elif k == "decision" and e.get("state") == "requested":
        print(f"DECISION-REQUEST {e['decision']} by {a}: {d}", flush=True)
