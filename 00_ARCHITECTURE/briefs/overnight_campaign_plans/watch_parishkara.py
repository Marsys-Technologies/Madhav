import sys, json

CY, YE, DIM, MAG, RST = "\033[1;36m", "\033[33m", "\033[2m", "\033[1;35m", "\033[0m"

for line in sys.stdin:
    line = line.strip()
    if not line.startswith("{"):
        continue
    try:
        e = json.loads(line)
    except Exception:
        continue
    t = e.get("type")
    if t == "assistant":
        for b in (e.get("message") or {}).get("content") or []:
            bt = b.get("type")
            if bt == "text" and b.get("text", "").strip():
                print(f"\n{CY}◆ CONDUCTOR:{RST} {b['text'].strip()}")
            elif bt == "tool_use":
                i = b.get("input", {}) or {}
                brief = i.get("description") or i.get("command") or i.get("prompt") or i.get("file_path") or json.dumps(i)[:100]
                print(f"  {YE}▸ {b.get('name','?')}{RST} {str(brief).replace(chr(10),' ')[:160]}")
    elif t == "user":
        for b in (e.get("message") or {}).get("content") or []:
            if b.get("type") == "tool_result":
                c = b.get("content")
                if isinstance(c, list):
                    c = " ".join(x.get("text", "") for x in c if isinstance(x, dict))
                s = str(c or "").replace("\n", " ")[:140]
                if s:
                    print(f"    {DIM}✓ {s}{RST}")
    elif t == "result":
        cost = e.get("total_cost_usd", 0) or 0
        print(f"\n{MAG}■ SESSION ENDED{RST} cost=${cost:.2f} turns={e.get('num_turns','?')} — supervisor relaunches in 90s")
