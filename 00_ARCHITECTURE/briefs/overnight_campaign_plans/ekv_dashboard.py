#!/usr/bin/env python3
"""
ekv_dashboard.py — simple live local dashboard for the EKAVAKYATA overnight run.

Stdlib only. Serves:
  GET /            -> static HTML/JS shell (polls /status.json every 5s)
  GET /status.json -> freshly computed status, read straight off real state:
                       supervisor RUN_DIR, origin/campaign-coordination,
                       ekv_manifest.json (once seeded), stream logs, ekv_gate.py.

No state is cached across requests — every hit re-reads the real files/git ref,
so what you see is always current as of that request, not a snapshot.
"""
import http.server, json, os, re, subprocess, time, datetime

SHAD = "/Users/Dev/shad_overnight"
REPO = "/Users/Dev/Vibe-Coding/Apps/Madhav"
RUN_DIR = os.path.expanduser("~/.ekv-overnight-supervisor")
PORT = 8765
CLOSE_TARGET_HOUR = 7  # 07:00 local time, per the conductor kickoff's CLOSE target
WALL_BUDGET_HOURS = 10

def sh(cmd, cwd=None, timeout=15):
    try:
        r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except Exception as e:
        return -1, "", str(e)

def supervisor_state():
    out = {"attempt": None, "started_at": None, "elapsed_min": None, "log_tail": []}
    attempt_f = os.path.join(RUN_DIR, "attempt")
    sup_log = os.path.join(RUN_DIR, "supervisor.log")
    if os.path.exists(attempt_f):
        out["attempt"] = open(attempt_f).read().strip()
    if os.path.exists(sup_log):
        lines = open(sup_log).read().splitlines()
        out["log_tail"] = lines[-12:]
        m = re.match(r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]", lines[0]) if lines else None
        if m:
            started = datetime.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
            out["started_at"] = m.group(1)
            out["elapsed_min"] = round((datetime.datetime.now() - started).total_seconds() / 60, 1)
    return out

def coordination_state():
    sh("git fetch origin campaign-coordination --quiet", cwd=REPO, timeout=20)
    rc, content, _ = sh(
        "git show origin/campaign-coordination:00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md",
        cwd=REPO,
    )
    if rc != 0:
        return {"available": False, "marker": "NONE", "recent_ekv_lines": []}
    marker = "NONE"
    # BUG FIX (2026-08-16 21:40, then again 23:40): first bug was a plain substring
    # check matching prose ("posts `RUN-TERMINAL: ...`"). The anchored-line fix that
    # followed then missed the ACTUAL close format, a decorated banner block
    # ("# ██ EKAVAKYATA-CLOSED-PARTIAL ██") that isn't a bare standalone line either.
    # Delegated to ekv_terminal_check.py, which checks the real distinguishing
    # feature (inline-backtick-quoted mention vs an actual posted marker) instead
    # of guessing at line shape.
    import subprocess
    term = subprocess.run(["python3", os.path.join(SHAD, "ekv_terminal_check.py")],
                           input=content, capture_output=True, text=True, timeout=5).stdout.strip()
    if term == "COMPLETE":
        marker = "COMPLETE"
    elif term == "PARTIAL":
        marker = "PARTIAL"
    ekv_lines = [l for l in content.splitlines() if "EKV" in l or "EKAVAKYATA" in l or "SŪTRADHĀRA" in l]
    return {"available": True, "marker": marker, "recent_ekv_lines": ekv_lines[-15:]}

def manifest_state():
    # CORRECTION (2026-08-16 02:15): this used to read the manifest from
    # origin/campaign-coordination via git. That is the WRONG source and made the
    # dashboard report a stale T0 skeleton for two hours while the real record
    # advanced. ekv_gate.py reads the manifest from the WORKING TREE
    # (os.path.join(repo, ...)), so the dashboard must read the same file the
    # gate does, or it is not showing the state that actually decides the night.
    path = os.path.join(REPO, "00_ARCHITECTURE/briefs/ekavakyata/ekv_manifest.json")
    if not os.path.exists(path):
        return {"seeded": False, "lanes": [], "by_status": {}, "pct_live": 0, "source": path}
    try:
        with open(path) as f:
            m = json.load(f)
    except Exception:
        return {"seeded": False, "lanes": [], "by_status": {}, "pct_live": 0, "parse_error": True, "source": path}
    lanes = m.get("lanes", [])
    by_status = {}
    for l in lanes:
        st = l.get("status", "?")
        by_status[st] = by_status.get(st, 0) + 1
    live = by_status.get("LIVE", 0)
    pct = round(100 * live / len(lanes), 1) if lanes else 0
    return {
        "seeded": True,
        "lanes": lanes,
        "by_status": by_status,
        "pct_live": pct,
        "deployed_catalog_version": m.get("deployed_catalog_version"),
        "deployed_main_sha": m.get("deployed_main_sha"),
        "source": path,
    }

def stream_state():
    out = {}
    logs_dir = os.path.join(SHAD, "ekv-logs")
    for letter in "ABCDE":
        f = os.path.join(logs_dir, f"stream_{letter}.log")
        if not os.path.exists(f):
            out[letter] = {"exists": False}
            continue
        st = os.stat(f)
        age_min = round((time.time() - st.st_mtime) / 60, 1)
        lines = open(f, errors="replace").read().splitlines()
        out[letter] = {
            "exists": True,
            "last_modified_min_ago": age_min,
            "last_line": lines[-1] if lines else "",
            "size_bytes": st.st_size,
        }
    return out

def gate_status():
    rc, out, err = sh(f"python3 {SHAD}/ekv_gate.py status --repo {REPO}", timeout=20)
    return {"rc": rc, "output": out.strip() or err.strip()}

def eta_state():
    now = datetime.datetime.now()
    target = now.replace(hour=CLOSE_TARGET_HOUR, minute=0, second=0, microsecond=0)
    if now >= target:
        target += datetime.timedelta(days=1)
    remaining_min = round((target - now).total_seconds() / 60, 1)
    return {"now": now.strftime("%Y-%m-%d %H:%M:%S"), "close_target": target.strftime("%Y-%m-%d %H:%M:%S"), "remaining_min_to_target": remaining_min}

def build_status():
    sup = supervisor_state()
    coord = coordination_state()
    man = manifest_state()
    streams = stream_state()
    eta = eta_state()
    gate = gate_status() if man["seeded"] else {"rc": None, "output": "manifest not yet seeded"}
    phase = "T0 SEEDING" if not man["seeded"] else ("CLOSED" if coord["marker"] in ("COMPLETE", "PARTIAL") else "EXECUTING")
    return {
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "phase": phase,
        "terminal_marker": coord["marker"],
        "supervisor": sup,
        "coordination": coord,
        "manifest": man,
        "streams": streams,
        "gate": gate,
        "eta": eta,
        "wall_budget_hours": WALL_BUDGET_HOURS,
    }

INDEX_HTML = """<!doctype html>
<html><head><meta charset="utf-8"><title>EKAVAKYATA — live</title>
<style>
body{font:14px/1.5 -apple-system,Menlo,monospace;background:#0d1117;color:#c9d1d9;margin:0;padding:24px}
h1{font-size:18px;color:#58a6ff;margin:0 0 4px}
.sub{color:#8b949e;margin-bottom:20px;font-size:12px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-bottom:20px}
.card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:14px}
.card .label{color:#8b949e;font-size:11px;text-transform:uppercase;letter-spacing:.5px}
.card .value{font-size:22px;margin-top:4px;color:#e6edf3}
.phase-EXECUTING{color:#3fb950}.phase-T0{color:#d29922}.phase-CLOSED{color:#58a6ff}
table{width:100%;border-collapse:collapse;margin-top:8px;font-size:12px}
td,th{padding:4px 8px;border-bottom:1px solid #21262d;text-align:left}
th{color:#8b949e;font-weight:normal}
pre{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:10px;overflow:auto;max-height:220px;font-size:11px;color:#8b949e}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px}
.LIVE .dot{background:#3fb950}.HANDOFF .dot,.BLOCKED .dot{background:#d29922}
.err{color:#f85149}
</style></head>
<body>
<h1>EKAVĀKYATĀ — overnight run</h1>
<div class="sub" id="genat">loading…</div>
<div class="grid" id="cards"></div>
<h3>Lane status</h3>
<table id="lanes"><thead><tr><th>Lane</th><th>Wave</th><th>Status</th><th>Branch</th></tr></thead><tbody></tbody></table>
<h3>Streams</h3>
<table id="streams"><thead><tr><th>Stream</th><th>Last activity</th><th>Last line</th></tr></thead><tbody></tbody></table>
<h3>Recent coordination markers</h3>
<pre id="markers"></pre>
<h3>Supervisor log tail</h3>
<pre id="suplog"></pre>
<script>
async function tick(){
  try {
    const r = await fetch('/status.json', {cache:'no-store'});
    const d = await r.json();
    document.getElementById('genat').textContent = 'as of ' + d.generated_at + ' · refreshes every 5s';
    const pctDone = d.manifest.pct_live;
    const cards = [
      ['Phase', d.phase],
      ['Terminal marker', d.terminal_marker],
      ['Lanes LIVE', pctDone + '%'],
      ['Attempt #', d.supervisor.attempt ?? '—'],
      ['Elapsed', d.supervisor.elapsed_min ? d.supervisor.elapsed_min + ' min' : '—'],
      ['Wall budget', d.wall_budget_hours + ' h'],
      ['ETA to 07:00 close', d.eta.remaining_min_to_target + ' min'],
    ];
    document.getElementById('cards').innerHTML = cards.map(([l,v]) =>
      `<div class="card"><div class="label">${l}</div><div class="value">${v}</div></div>`).join('');

    const lanesBody = (d.manifest.lanes || []).map(l =>
      `<tr class="${l.status}"><td><span class="dot"></span>${l.lane}</td><td>${l.wave}</td><td>${l.status}</td><td>${l.branch||''}</td></tr>`
    ).join('') || '<tr><td colspan=4 class="err">manifest not seeded yet</td></tr>';
    document.querySelector('#lanes tbody').innerHTML = lanesBody;

    const streamRows = Object.entries(d.streams).map(([k,v]) =>
      v.exists
        ? `<tr><td>${k}</td><td>${v.last_modified_min_ago} min ago</td><td>${(v.last_line||'').slice(0,120)}</td></tr>`
        : `<tr><td>${k}</td><td colspan=2 class="err">not launched yet</td></tr>`
    ).join('');
    document.querySelector('#streams tbody').innerHTML = streamRows;

    document.getElementById('markers').textContent = (d.coordination.recent_ekv_lines||[]).join('\\n') || '(none yet)';
    document.getElementById('suplog').textContent = (d.supervisor.log_tail||[]).join('\\n');
  } catch(e) {
    document.getElementById('genat').textContent = 'fetch error: ' + e;
  }
  setTimeout(tick, 5000);
}
tick();
</script>
</body></html>"""

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # keep stdout quiet

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            body = INDEX_HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/status.json":
            try:
                body = json.dumps(build_status(), indent=2).encode()
                code = 200
            except Exception as e:
                body = json.dumps({"error": str(e)}).encode()
                code = 500
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404); self.end_headers()

if __name__ == "__main__":
    print(f"EKAVAKYATA dashboard on http://localhost:{PORT}/")
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
