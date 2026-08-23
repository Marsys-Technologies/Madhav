#!/usr/bin/env python3
"""Live view of the autonomous conductor session — chat-style rendering.

Follows whichever session is currently active, and automatically switches when
the supervisor relaunches the conductor. Read-only: never touches the run.
Ctrl+C to stop watching.
"""
import json, os, re, shutil, sys, time, glob

PROJ = "/Users/Dev/.claude/projects/-Users-Dev-Vibe-Coding-Apps-Madhav"
SELF = "2917831b-6d2c-4001-9e28-4d390929e0f7"          # the strategy-desk conversation

C = {
    "dim":   "\033[2m",   "reset": "\033[0m",  "bold": "\033[1m",
    "cyan":  "\033[36m",  "green": "\033[32m", "yellow": "\033[33m",
    "mag":   "\033[35m",  "red":   "\033[31m", "blue":  "\033[34m",
}
W = min(shutil.get_terminal_size((100, 30)).columns, 110)


def wrap(text, indent="   "):
    out = []
    for para in text.split("\n"):
        if not para.strip():
            out.append("")
            continue
        line = indent
        for word in para.split():
            if len(line) + len(word) + 1 > W:
                out.append(line)
                line = indent + word
            else:
                line = (line + " " + word) if line.strip() else indent + word
        out.append(line)
    return "\n".join(out)


def newest_session():
    files = [f for f in glob.glob(os.path.join(PROJ, "*.jsonl")) if SELF not in f]
    if not files:
        return None
    f = max(files, key=os.path.getmtime)
    # only consider it "active" if touched recently
    return f if (time.time() - os.path.getmtime(f)) < 900 else None


def render(evt):
    if evt.get("type") != "assistant":
        return
    for b in (evt.get("message") or {}).get("content") or []:
        t = b.get("type")
        ts = time.strftime("%H:%M:%S")
        if t == "text" and b.get("text", "").strip():
            print(f"\n{C['cyan']}{C['bold']}🤖 CONDUCTOR{C['reset']} {C['dim']}{ts}{C['reset']}")
            print(f"{C['cyan']}{wrap(b['text'])}{C['reset']}")
        elif t == "tool_use":
            name, inp = b.get("name", "?"), b.get("input", {})
            if name == "Agent":
                who = str(inp.get("description", ""))[:70]
                print(f"  {C['mag']}🚀 DISPATCH SUBAGENT{C['reset']} {C['bold']}{who}{C['reset']}")
            elif name == "Task":
                print(f"  {C['mag']}🚀 TASK{C['reset']} {str(inp)[:80]}")
            elif name == "Bash":
                cmd = re.sub(r"\s+", " ", str(inp.get("command", "")))[:95]
                print(f"  {C['dim']}⚙ $ {cmd}{C['reset']}")
            elif name in ("Write", "Edit", "Read"):
                p = str(inp.get("file_path", ""))
                p = p.replace("/Users/Dev/Vibe-Coding/Apps/Madhav/", "")
                icon = {"Write": "✏️ write", "Edit": "✏️ edit", "Read": "📖 read"}[name]
                print(f"  {C['dim']}{icon} {p[:90]}{C['reset']}")
            elif name == "TodoWrite":
                todos = inp.get("todos", [])
                active = [t.get("content", "")[:60] for t in todos
                          if t.get("status") == "in_progress"]
                if active:
                    print(f"  {C['yellow']}📋 now: {active[0]}{C['reset']}")
            else:
                print(f"  {C['dim']}⚙ {name}: {str(inp)[:85]}{C['reset']}")


def main():
    cur, fh, pos = None, None, 0
    print(f"{C['bold']}ŚABDA-ŚUDDHI — live conductor view{C['reset']}")
    print(f"{C['dim']}follows session relaunches automatically · Ctrl+C to stop "
          f"(does not affect the run){C['reset']}")
    try:
        while True:
            f = newest_session()
            if f is None:
                print(f"{C['red']}… no active conductor session (checking every 15s){C['reset']}")
                time.sleep(15)
                continue
            if f != cur:
                if fh:
                    fh.close()
                cur, pos = f, 0
                fh = open(f, "r")
                print(f"\n{C['green']}{'═' * (W - 2)}{C['reset']}")
                print(f"{C['green']}{C['bold']}▶ attached: {os.path.basename(f)}{C['reset']}")
                print(f"{C['green']}{'═' * (W - 2)}{C['reset']}")
                # show the tail of what already happened, then follow
                lines = fh.readlines()
                for line in lines[-60:]:
                    try:
                        render(json.loads(line))
                    except Exception:
                        pass
                pos = fh.tell()
            fh.seek(pos)
            new = fh.readlines()
            pos = fh.tell()
            for line in new:
                try:
                    render(json.loads(line))
                except Exception:
                    pass
            sys.stdout.flush()
            time.sleep(2)
    except KeyboardInterrupt:
        print(f"\n{C['dim']}stopped watching — the run continues.{C['reset']}")


if __name__ == "__main__":
    main()
