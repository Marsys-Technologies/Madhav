#!/usr/bin/env python3
"""Token-economy baseline for the Madhav project (read-only).

Reads, never writes, the local usage records and reports the four usage
classes separately -- input (uncached), output, cache_creation, cache_read --
plus their total, broken down by day, ISO week, model, session, workspace
(campaign / branch / worktree) and role.

Sources
  claude  ~/.claude/projects/**/*.jsonl  (main + subagent/sidechain transcripts)
          One assistant message is written as several lines (one per content
          block) that repeat the same usage; rows are de-duplicated on
          (message.id, requestId) and the last-seen usage wins.
  codex   ~/.codex/sessions/**/rollout-*.jsonl  (final cumulative token_count
          per session; input is split into uncached + cached; reasoning tokens
          are a subset of output and reported as a side column).
  fleet   /Users/Dev/kalayantra/logs/<role>.<cycle>.log  (Codex exec transcripts:
          header model/effort/session id, the "tokens used" footer, IDLE-OK).

Usage
  token_baseline.py [--since YYYY-MM-DD] [--until YYYY-MM-DD] [--json OUT]
                    [--md OUT] [--waste] [--jobs N]

Only Madhav-related workspaces are counted (see is_madhav()).  Days are UTC.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import glob
import json
import os
import re
import statistics
import sys
from concurrent.futures import ProcessPoolExecutor

HOME = os.path.expanduser("~")
CLAUDE_ROOT = os.path.join(HOME, ".claude", "projects")
CODEX_ROOT = os.path.join(HOME, ".codex", "sessions")
FLEET_LOGS = "/Users/Dev/kalayantra/logs"
CLASSES = ("input", "output", "cache_creation", "cache_read")

# Matched on a normalised form ("/", "." and "_" -> "-", lower-case) so both real
# cwds and Claude Code's encoded project-folder names hit the same tokens.
MADHAV_TOKENS = (
    "madhav", "kalayantra", "nirmana", "suvarna", "pravaha",
    "-codex-worktrees-purna", "-codex-worktrees-journey", "-codex-worktrees-portal-",
    "-codex-worktrees-lel-", "-codex-worktrees-observatory", "-codex-worktrees-ai-circle",
    "-codex-worktrees-jataka",
)


def is_madhav(path: str) -> bool:
    if not path:
        return False
    n = re.sub(r"[/._]", "-", path).lower()
    return any(t in n for t in MADHAV_TOKENS)


def workspace_of(cwd: str) -> str:
    """Collapse a cwd to a campaign/worktree label."""
    if not cwd:
        return "?"
    m = re.search(r"/kalayantra/wt/([^/]+)", cwd)
    if m:
        return f"kalayantra/{m.group(1)}"
    if "/kalayantra" in cwd:
        return "kalayantra/root"
    for pat, lab in ((r"/\.codex/worktrees/([^/]+)", "codex-wt/"),
                     (r"/\.claude/worktrees/([^/]+)", "claude-wt/"),
                     (r"/worktrees\.noindex/madhav/[^/]+/([^/]+)", "wt.noindex/"),
                     (r"/(nirmana-[^/]+)", ""), (r"/(madhav-[^/]+(?:/[^/]+)?)", "")):
        m = re.search(pat, cwd)
        if m:
            return lab + m.group(1)
    if "-Vibe-Coding-Apps-Madhav" in cwd or "/scratchpad" in cwd:
        return "claude-scratchpad"
    if cwd.rstrip("/").endswith("/Vibe-Coding/Apps/Madhav"):
        return "shared-checkout"
    if "/Vibe-Coding/Apps/Madhav/" in cwd:
        return "shared-checkout/" + cwd.split("/Vibe-Coding/Apps/Madhav/", 1)[1].split("/")[0]
    return cwd[-60:]


def role_of(workspace: str, sidechain: bool) -> str:
    m = re.match(r"kalayantra/(.+)", workspace)
    if m:
        lane = m.group(1)
        if re.fullmatch(r"k\d+", lane):
            return "KARAKA"
        if re.fullmatch(r"v\d+", lane):
            return "PARIKSAKA"
        return {"adhikarin": "ADHIKARIN", "sutradhara": "SUTRADHARA",
                "root": "interactive(kalayantra-root)", "campaign": "interactive(kalayantra-campaign)"}.get(lane, lane.upper())
    m = re.match(r"nirmana-s-(.+)", workspace)
    if m:
        return "NIRMANA-" + m.group(1).upper()
    return "subagent" if sidechain else "interactive"


def iso_week(day: str) -> str:
    y, w, _ = dt.date.fromisoformat(day).isocalendar()
    return f"{y}-W{w:02d}"


def zero():
    return dict.fromkeys(CLASSES, 0)


def add(a, b):
    for k in CLASSES:
        a[k] += b.get(k, 0)


def total(u):
    return sum(u[k] for k in CLASSES)


# ---------------------------------------------------------------- claude ----
def _content_len(c) -> int:
    if isinstance(c, str):
        return len(c)
    if isinstance(c, list):
        n = 0
        for b in c:
            if isinstance(b, dict):
                if b.get("type") == "text":
                    n += len(b.get("text", ""))
                elif b.get("type") == "image":
                    n += len(json.dumps(b.get("source", {}))) // 4
                else:
                    n += len(json.dumps(b))
        return n
    return len(json.dumps(c)) if c is not None else 0


def parse_claude_file(path: str):
    """Return per-call usage rows and per-file waste signals."""
    calls = {}             # (msg_id, request_id) -> row
    tool_names = {}        # tool_use_id -> name
    tool_results = []      # (chars, tool)
    reads = collections.Counter()
    turns = 0
    compactions = 0
    session = cwd = branch = None
    sidechain = "/subagents/" in path
    try:
        fh = open(path, errors="replace")
    except OSError:
        return None
    with fh:
        for line in fh:
            try:
                o = json.loads(line)
            except ValueError:
                continue
            t = o.get("type")
            session = session or o.get("sessionId")
            cwd = o.get("cwd") or cwd
            branch = o.get("gitBranch") or branch
            if o.get("isSidechain"):
                sidechain = True
            if t == "system" and o.get("subtype") == "compact_boundary":
                compactions += 1
            msg = o.get("message") or {}
            if t == "assistant" and isinstance(msg, dict):
                u = msg.get("usage") or {}
                key = (msg.get("id"), o.get("requestId"))
                if u and key[0]:
                    prev = calls.get(key)
                    row = {
                        "ts": o.get("timestamp", ""),
                        "model": msg.get("model", "?"),
                        "input": u.get("input_tokens", 0) or 0,
                        "output": u.get("output_tokens", 0) or 0,
                        "cache_creation": u.get("cache_creation_input_tokens", 0) or 0,
                        "cache_read": u.get("cache_read_input_tokens", 0) or 0,
                    }
                    if prev:   # partial usage on early content-block lines: keep max
                        for k in CLASSES:
                            row[k] = max(row[k], prev[k])
                    calls[key] = row
                for b in msg.get("content") or []:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        tool_names[b.get("id")] = b.get("name", "?")
                        if b.get("name") == "Read":
                            fp = (b.get("input") or {}).get("file_path")
                            if fp:
                                reads[fp] += 1
            elif t == "user" and isinstance(msg, dict):
                content = msg.get("content")
                is_tool = False
                if isinstance(content, list):
                    for b in content:
                        if isinstance(b, dict) and b.get("type") == "tool_result":
                            is_tool = True
                            tool_results.append((_content_len(b.get("content")),
                                                 tool_names.get(b.get("tool_use_id"), "?")))
                if not is_tool and not o.get("isMeta") and not o.get("isCompactSummary"):
                    turns += 1
    if not calls:
        return None
    return {
        "path": path, "session": session or os.path.basename(path),
        "cwd": cwd or "", "branch": branch or "", "sidechain": sidechain,
        "calls": calls, "tool_results": tool_results,
        "rereads": {k: v for k, v in reads.items() if v > 1},
        "reads_total": sum(reads.values()), "turns": turns,
        "compactions": compactions,
    }


# ----------------------------------------------------------------- codex ----
def parse_codex_file(path: str):
    meta, model, effort, last, rl, ts0 = {}, "?", "?", None, None, None
    try:
        with open(path, errors="replace") as fh:
            for line in fh:
                if '"session_meta"' not in line and '"turn_context"' not in line \
                        and '"token_count"' not in line:
                    continue
                try:
                    o = json.loads(line)
                except ValueError:
                    continue
                p = o.get("payload") or {}
                if o.get("type") == "session_meta":
                    meta = p
                    ts0 = p.get("timestamp") or o.get("timestamp")
                elif o.get("type") == "turn_context":
                    model = p.get("model", model)
                    effort = p.get("effort", effort)
                elif p.get("type") == "token_count" and p.get("info"):
                    last = p["info"].get("total_token_usage")
                    rl = p.get("rate_limits") or rl
    except OSError:
        return None
    if not last:
        return None
    inp = last.get("input_tokens", 0)
    cached = last.get("cached_input_tokens", 0)
    return {
        "path": path, "session": meta.get("id") or meta.get("session_id"),
        "cwd": meta.get("cwd", ""), "ts": ts0 or "", "model": model,
        "effort": effort, "source": meta.get("source", "?"),
        "usage": {"input": max(inp - cached, 0), "output": last.get("output_tokens", 0),
                  "cache_creation": last.get("cache_write_input_tokens", 0) or 0,
                  "cache_read": cached},
        "reasoning": last.get("reasoning_output_tokens", 0),
        "rate_limits": rl,
    }


# ----------------------------------------------------------------- fleet ----
FLEET_RE = re.compile(r"^([a-z]+\d*)\.(\d+)\.log$")


def parse_fleet_log(path: str):
    name = os.path.basename(path)
    m = FLEET_RE.match(name)
    if not m:
        return None
    head = tail = ""
    try:
        with open(path, "rb") as fh:
            head = fh.read(2048).decode("utf-8", "replace")
            fh.seek(max(os.path.getsize(path) - 4096, 0))
            tail = fh.read().decode("utf-8", "replace")
    except OSError:
        return None
    if head.lstrip().startswith("{"):       # claude -p stream-json lane
        usage, model = zero(), None
        found = False
        with open(path, errors="replace") as fh:
            for line in fh:
                if '"type":"result"' not in line and '"type": "result"' not in line:
                    if model is None and '"model"' in line and '"init"' in line:
                        try:
                            model = json.loads(line).get("model")
                        except ValueError:
                            pass
                    continue
                try:
                    o = json.loads(line)
                except ValueError:
                    continue
                u = o.get("usage") or {}
                found = True
                usage["input"] += u.get("input_tokens", 0) or 0
                usage["output"] += u.get("output_tokens", 0) or 0
                usage["cache_creation"] += u.get("cache_creation_input_tokens", 0) or 0
                usage["cache_read"] += u.get("cache_read_input_tokens", 0) or 0
        return {"lane": m.group(1), "cycle": int(m.group(2)), "mtime": os.path.getmtime(path),
                "model": model or "claude?", "effort": "?", "session": None,
                "tokens_used": None, "claude_usage": usage if found else None,
                "idle": "IDLE-OK" in tail, "bytes": os.path.getsize(path)}
    g = lambda k: (re.search(rf"^{k}: (.+)$", head, re.M) or [None, None])[1]
    used = re.findall(r"tokens used\s*\n\s*([\d,]+)", tail)
    return {
        "lane": m.group(1), "cycle": int(m.group(2)), "mtime": os.path.getmtime(path),
        "model": g("model"), "effort": g("reasoning effort"), "session": g("session id"),
        "tokens_used": int(used[-1].replace(",", "")) if used else None,
        "idle": "IDLE-OK" in tail, "bytes": os.path.getsize(path), "claude_usage": None,
    }


# ------------------------------------------------------------ aggregation ---
def in_window(ts: str, since, until) -> bool:
    d = ts[:10]
    return bool(d) and (not since or d >= since) and (not until or d <= until)


def pct(xs, q):
    if not xs:
        return None
    xs = sorted(xs)
    return xs[min(int(q * len(xs)), len(xs) - 1)]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--since")
    ap.add_argument("--until")
    ap.add_argument("--json")
    ap.add_argument("--md")
    ap.add_argument("--waste", action="store_true", help="include waste-pattern sections")
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 4)
    a = ap.parse_args(argv)

    claude_files = [f for f in glob.glob(CLAUDE_ROOT + "/**/*.jsonl", recursive=True)
                    if is_madhav(f)]
    codex_files = glob.glob(CODEX_ROOT + "/**/rollout-*.jsonl", recursive=True)
    fleet_files = glob.glob(FLEET_LOGS + "/*.log")
    with ProcessPoolExecutor(a.jobs) as ex:
        cl = [r for r in ex.map(parse_claude_file, claude_files, chunksize=8) if r]
        cx = [r for r in ex.map(parse_codex_file, codex_files, chunksize=16) if r]
        fl = [r for r in map(parse_fleet_log, fleet_files) if r]
    cx = [r for r in cx if is_madhav(r["cwd"])]

    # Global de-duplication: resumed/forked sessions copy history into new files.
    seen = {}
    for f in cl:
        for key, row in f["calls"].items():
            if key in seen:
                prev = seen[key][1]
                for k in CLASSES:
                    prev[k] = max(prev[k], row[k])
            else:
                seen[key] = (id(f), row)
    owner = collections.defaultdict(list)
    for key, (fid, row) in seen.items():
        owner[fid].append(row)
    dup_keys = sum(len(f["calls"]) for f in cl) - len(seen)
    for f in cl:
        f["calls"] = owner.get(id(f), [])

    by = {k: collections.defaultdict(zero) for k in
          ("provider", "day", "week", "model", "workspace", "role", "session", "model_role")}
    sess_meta = {}
    ctx_sizes, out_sizes = [], []
    calls_n = 0
    for f in cl:
        ws = workspace_of(f["cwd"])
        role = role_of(ws, f["sidechain"])
        sid = "claude:" + f["session"]
        for c in f["calls"]:
            if not in_window(c["ts"], a.since, a.until):
                continue
            calls_n += 1
            day = c["ts"][:10]
            for dim, key in (("provider", "claude"), ("day", day), ("week", iso_week(day)),
                             ("model", c["model"]), ("workspace", ws), ("role", role),
                             ("session", sid), ("model_role", f'{c["model"]} | {role}')):
                add(by[dim][key], c)
            ctx_sizes.append(c["input"] + c["cache_creation"] + c["cache_read"])
            out_sizes.append(c["output"])
            sm = sess_meta.setdefault(sid, {"workspace": ws, "branch": f["branch"], "role": role,
                                            "turns": 0, "calls": 0, "first": day, "subagent_files": 0})
            sm["calls"] += 1
            sm["first"] = min(sm["first"], day)
        if sid in sess_meta:
            sm = sess_meta[sid]
            if f["sidechain"]:
                sm["subagent_files"] += 1
            else:
                sm["turns"] += f["turns"]
    codex_reasoning = 0
    latest_rl = None
    for r in cx:
        if not in_window(r["ts"], a.since, a.until):
            continue
        day = r["ts"][:10]
        ws = workspace_of(r["cwd"])
        role = role_of(ws, False)
        sid = "codex:" + str(r["session"])
        u = r["usage"]
        codex_reasoning += r["reasoning"]
        for dim, key in (("provider", "codex"), ("day", day), ("week", iso_week(day)),
                         ("model", f'{r["model"]} ({r["effort"]})'), ("workspace", ws),
                         ("role", role), ("session", sid),
                         ("model_role", f'{r["model"]} ({r["effort"]}) | {role}')):
            add(by[dim][key], u)
        sess_meta[sid] = {"workspace": ws, "branch": "", "role": role, "turns": None,
                          "calls": None, "first": day, "subagent_files": 0}
        if r["rate_limits"] and (latest_rl is None or r["ts"] > latest_rl[0]):
            latest_rl = (r["ts"], r["rate_limits"])


    def table(dim, top=None):
        rows = sorted(by[dim].items(), key=lambda kv: -total(kv[1]))
        return [{"key": k, **v, "total": total(v)} for k, v in (rows[:top] if top else rows)]

    fleet_win = [r for r in fl if in_window(dt.datetime.fromtimestamp(r["mtime"], dt.timezone.utc).isoformat(),
                                            a.since, a.until)]
    fleet_roles = collections.defaultdict(lambda: {"cycles": 0, "idle": 0, "tokens_used": 0,
                                                   "idle_tokens_used": 0, "no_footer": 0,
                                                   "claude_cycles": 0, "claude_usage": zero(),
                                                   "models": collections.Counter()})
    for r in fleet_win:
        lane = r["lane"]
        role = role_of("kalayantra/" + lane, False)
        fr = fleet_roles[role]
        fr["cycles"] += 1
        fr["models"][f'{r["model"]} ({r["effort"]})'] += 1
        if r.get("claude_usage"):
            fr["claude_cycles"] += 1
            add(fr["claude_usage"], r["claude_usage"])
            # claude -p lanes write no transcript: add to the four-class totals
            day = dt.datetime.fromtimestamp(r["mtime"], dt.timezone.utc).date().isoformat()
            for dim, key in (("provider", "claude(fleet-stream-json)"), ("day", day), ("week", iso_week(day)),
                             ("model", r["model"]), ("workspace", "kalayantra/" + lane), ("role", role),
                             ("model_role", f'{r["model"]} | {role}')):
                add(by[dim][key], r["claude_usage"])
            continue
        if r["tokens_used"] is None:
            fr["no_footer"] += 1
            continue
        fr["tokens_used"] += r["tokens_used"]
        if r["idle"]:
            fr["idle"] += 1
            fr["idle_tokens_used"] += r["tokens_used"]
    for v in fleet_roles.values():
        v["models"] = dict(v["models"])

    grand = zero()
    for v in by["provider"].values():
        add(grand, v)

    claude_sessions = [(s, m) for s, m in sess_meta.items() if s.startswith("claude:")]
    turns = [m["turns"] for _, m in claude_sessions if m["turns"]]
    out = {
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "window": {"since": a.since, "until": a.until},
        "sources": {"claude_files": len(claude_files), "claude_files_with_usage": len(cl),
                    "codex_files_scanned": len(codex_files), "codex_madhav_sessions": len(cx),
                    "fleet_logs": len(fl), "claude_api_calls_deduped": calls_n,
                    "claude_cross_file_duplicate_keys_dropped": dup_keys},
        "grand_total": {**grand, "total": total(grand)},
        "codex_reasoning_tokens_subset_of_output": codex_reasoning,
        "shares": {"cache_read_share": grand["cache_read"] / max(total(grand), 1),
                   "output_share": grand["output"] / max(total(grand), 1)},
        "by_provider": table("provider"), "by_week": sorted(table("week"), key=lambda r: r["key"]),
        "by_day": sorted(table("day"), key=lambda r: r["key"]),
        "by_model": table("model"), "by_workspace": table("workspace", 40),
        "by_role": table("role"), "by_model_role": table("model_role", 25),
        "claude_first_day": min((m["first"] for s_, m in sess_meta.items() if s_.startswith("claude:")), default=None),
        "top_sessions": [{**r, **sess_meta.get(r["key"], {})} for r in table("session", 20)],
        "claude_session_turns": {"n": len(turns), "p50": pct(turns, .5), "p90": pct(turns, .9),
                                 "max": max(turns) if turns else None},
        "claude_per_call_context_tokens": {"n": len(ctx_sizes), "p50": pct(ctx_sizes, .5),
                                           "p90": pct(ctx_sizes, .9), "p99": pct(ctx_sizes, .99),
                                           "mean": statistics.fmean(ctx_sizes) if ctx_sizes else None},
        "claude_per_call_output_tokens": {"p50": pct(out_sizes, .5), "p90": pct(out_sizes, .9)},
        "fleet_cycle_logs": {"note": "'tokens used' is the Codex exec footer (single blended figure, "
                                     "convention per Codex CLI); four-class split comes from the codex source",
                             "by_role": dict(fleet_roles)},
        "codex_latest_rate_limits": latest_rl[1] if latest_rl else None,
    }

    if a.waste:
        tr = collections.defaultdict(lambda: [0, 0, 0])   # tool -> n, chars, max
        biggest = []
        rereads = []
        comp = 0
        for f in cl:
            comp += f["compactions"]
            for n, tool in f["tool_results"]:
                t = tr[tool]
                t[0] += 1
                t[1] += n
                t[2] = max(t[2], n)
                biggest.append((n, tool, workspace_of(f["cwd"])))
            if f["rereads"]:
                rereads.append((sum(v - 1 for v in f["rereads"].values()), f["session"],
                                workspace_of(f["cwd"]),
                                sorted(f["rereads"].items(), key=lambda kv: -kv[1])[:3]))
        out["waste"] = {
            "tool_result_chars_by_tool": sorted(
                ({"tool": k, "n": v[0], "chars": v[1], "est_tokens_chars_div4": v[1] // 4,
                  "max_chars": v[2]} for k, v in tr.items()), key=lambda r: -r["chars"])[:25],
            "largest_tool_results": [{"chars": n, "tool": t, "workspace": w}
                                     for n, t, w in sorted(biggest, reverse=True)[:20]],
            "files_with_rereads": len(rereads),
            "redundant_reads_total": sum(r[0] for r in rereads),
            "reads_total": sum(f["reads_total"] for f in cl),
            "top_reread_files": [{"redundant_reads": r[0], "session": r[1], "workspace": r[2],
                                  "top": r[3]} for r in sorted(rereads, reverse=True)[:10]],
            "compaction_events": comp,
            "transcripts_with_compaction": sum(1 for f in cl if f["compactions"]),
        }

    if a.json:
        with open(a.json, "w") as fh:
            json.dump(out, fh, indent=1, default=str)
    if a.md:
        with open(a.md, "w") as fh:
            fh.write(render_md(out))
    if not a.json and not a.md:
        print(render_md(out))
    return 0


def fmt(n):
    return f"{n:,}" if isinstance(n, int) else ("" if n is None else str(n))


def render_md(o):
    L = [f"# Token baseline ({o['generated_utc']})",
         f"Window: {o['window']}  Sources: {o['sources']}", ""]
    hdr = "| key | input | output | cache_creation | cache_read | total |\n|---|--:|--:|--:|--:|--:|"

    def tab(title, rows):
        L.append(f"## {title}\n{hdr}")
        for r in rows:
            L.append(f"| {r['key']} | " + " | ".join(fmt(r[k]) for k in (*CLASSES, "total")) + " |")
        L.append("")
    g = o["grand_total"]
    tab("Grand total", [{"key": "all", **g}])
    L.append(f"cache_read share {o['shares']['cache_read_share']:.1%}; output share "
             f"{o['shares']['output_share']:.2%}; codex reasoning (subset of output) "
             f"{fmt(o['codex_reasoning_tokens_subset_of_output'])}\n")
    for k, t in (("by_provider", "By provider"), ("by_week", "By ISO week"), ("by_model", "By model"),
                 ("by_role", "By role"), ("by_model_role", "By model x role (top 25)"), ("by_workspace", "By workspace (top 40)"),
                 ("top_sessions", "Top 20 sessions")):
        tab(t, o[k])
    L.append("Top-session context: " + "; ".join(f"{r['key'][:15]} ws={r.get('workspace')} role={r.get('role')} turns={r.get('turns')} calls={r.get('calls')} subagent_files={r.get('subagent_files')} first={r.get('first')}" for r in o["top_sessions"][:10]) + "\n")
    L.append(f"Claude transcripts earliest day in window: {o.get('claude_first_day')}\n")
    L.append(f"Claude session turns: {o['claude_session_turns']}")
    L.append(f"Claude per-call context tokens: {o['claude_per_call_context_tokens']}")
    L.append(f"Claude per-call output tokens: {o['claude_per_call_output_tokens']}\n")
    L.append("## Fleet cycle logs (Codex exec footer)\n| role | cycles | idle | tokens_used | idle tokens_used | no footer | models |\n|---|--:|--:|--:|--:|--:|---|")
    for r, v in sorted(o["fleet_cycle_logs"]["by_role"].items()):
        L.append(f"| {r} | {v['cycles']} | {v['idle']} | {fmt(v['tokens_used'])} | "
                 f"{fmt(v['idle_tokens_used'])} | {v['no_footer']} | {v['models']} |")
    if "waste" in o:
        w = o["waste"]
        L.append("\n## Waste: tool-result volume by tool\n| tool | n | chars | est tokens (chars/4) | max |\n|---|--:|--:|--:|--:|")
        for r in w["tool_result_chars_by_tool"]:
            L.append(f"| {r['tool']} | {r['n']} | {fmt(r['chars'])} | {fmt(r['est_tokens_chars_div4'])} | {fmt(r['max_chars'])} |")
        L.append(f"\nRedundant re-reads: {w['redundant_reads_total']} of {w['reads_total']} Read calls "
                 f"({w['files_with_rereads']} transcripts). Compactions: {w['compaction_events']} in "
                 f"{w['transcripts_with_compaction']} transcripts.")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    sys.exit(main())
