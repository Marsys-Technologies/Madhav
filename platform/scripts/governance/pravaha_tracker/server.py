"""Pravāha tracker — a local, real-time dashboard server.

    python -m pravaha_tracker.server [--port 8766]      (run from platform/scripts/governance)

Real time: one engine thread ticks every second. It tails the event log, reloads the plan model if
it changed, schedules detectors whose TTL expired (and immediately re-checks the detector of any item
an event just touched), refreshes each stream's git activity every 20 s, and — whenever anything
changed — rebuilds the snapshot and pushes it to every open browser over Server-Sent Events.

Resilience:
- binds to 127.0.0.1 only and is read-only (no endpoint changes anything);
- every input is optional: a missing file, a dead database or a failing detector degrades that part
  of the view with an explicit error, never the whole page;
- the snapshot is written atomically to $PRAVAHA_HOME/run/snapshot.json on every change, so a
  restart shows the last state at once and the CLI can read it even when the server is down;
- the event log is copied to $PRAVAHA_HOME/run/backup/ every 10 minutes (14 daily files kept);
- launchd (KeepAlive) or run_tracker.sh restarts the server if it ever exits;
- the page shows its own freshness, switches to polling if the stream drops, and says so.
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import hashlib
import json
import os
import shutil
import sys
import threading
import time
import traceback
import collections
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    __package__ = "pravaha_tracker"

from pravaha_tracker import detectors as D  # noqa: E402
from pravaha_tracker.events import EventLog  # noqa: E402
from pravaha_tracker.state import build_snapshot  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
STATIC = os.path.join(HERE, "static")
DEFAULT_PORT = 8766


def default_config() -> dict:
    home = os.environ.get("PRAVAHA_HOME", "/Users/Dev/pravaha")
    return {
        "home": home,
        "events": os.environ.get("PRAVAHA_EVENTS", os.path.join(home, "run", "EVENTS.jsonl")),
        "snapshot": os.path.join(home, "run", "snapshot.json"),
        "backup_dir": os.path.join(home, "run", "backup"),
        "hold": os.path.join(home, "run", "PRAVAHA_HOLD"),
        "model": os.environ.get("PRAVAHA_PLAN_MODEL",
                                os.path.join(REPO_ROOT, "00_ARCHITECTURE", "control", "pravaha", "plan_model.json")),
        "repo": os.environ.get("PRAVAHA_REPO", REPO_ROOT),
        "pgenv": os.environ.get("PRAVAHA_PGENV") or None,
        "db_port": int(os.environ.get("PRAVAHA_DB_PORT", "5433")),
        "detectors_enabled": os.environ.get("PRAVAHA_DETECTORS", "1") != "0",
        "git_every_s": int(os.environ.get("PRAVAHA_GIT_EVERY_S", "20")),
        "backup_every_s": int(os.environ.get("PRAVAHA_BACKUP_EVERY_S", "600")),
    }


class Engine:
    """Owns all state; one background thread keeps it current."""

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.started_at = dt.datetime.now(dt.timezone.utc)
        self.log = EventLog(cfg["events"])
        self.det = D.Detectors(D.Config(repo=cfg["repo"], pgenv=cfg["pgenv"], home=cfg["home"]),
                               on_change=self._mark_dirty)
        self.model: dict = {"tracks": [], "items": [], "decisions": [], "streams": []}
        self.model_error: str | None = None
        self._model_mtime = None
        self.activity: dict = {}
        self._activity_at = 0.0
        self._activity_running = False
        self._backup_at = 0.0
        self._backup_info: dict = {}
        self._seen_events = 0
        self.snapshot: dict = {}
        self.version = 0
        self._digest = ""
        self._dirty = True
        self._last_tick = time.time()
        self._last_build = 0.0
        self.cond = threading.Condition()
        self._stop = threading.Event()
        self.tick_errors: collections.deque = collections.deque(maxlen=20)
        self._load_persisted()

    # ---- lifecycle ---------------------------------------------------------------------------
    def _load_persisted(self) -> None:
        try:
            with open(self.cfg["snapshot"], encoding="utf-8") as f:
                snap = json.load(f)
            snap.setdefault("health", {})["restored_from_disk"] = True
            self.snapshot, self.version = snap, int(snap.get("version", 0))
        except (OSError, ValueError):
            pass

    def start(self) -> None:
        threading.Thread(target=self._loop, name="engine", daemon=True).start()

    def stop(self) -> None:
        self._stop.set()

    def _mark_dirty(self) -> None:
        self._dirty = True

    # ---- the loop ----------------------------------------------------------------------------
    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self.tick()
            except Exception:  # the loop must never die
                self.tick_errors.append(dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
                                        + " " + traceback.format_exc(limit=2)[-400:])
            self._stop.wait(1.0)

    def tick(self) -> None:
        self._last_tick = time.time()
        self._reload_model()
        if self.log.refresh():
            self._dirty = True
            self._recheck_touched()
        if self.cfg["detectors_enabled"]:
            self.det.poll([i["detector"] for i in self.model.get("items", []) if i.get("detector")])
        if time.time() - self._activity_at > self.cfg["git_every_s"] and not self._activity_running:
            self._activity_running = True
            threading.Thread(target=self._refresh_activity, name="git-activity", daemon=True).start()
        if time.time() - self._backup_at > self.cfg["backup_every_s"]:
            self._backup()
        if self._dirty or time.time() - self._last_build > 5:
            self._dirty = False
            self._rebuild()

    def _recheck_touched(self) -> None:
        """An item event just arrived: re-measure that item's detector now, not at its next TTL."""
        new = self.log.events[self._seen_events:]
        self._seen_events = len(self.log.events)
        specs = {i["id"]: i["detector"] for i in self.model.get("items", []) if i.get("detector")}
        for ev in new:
            spec = specs.get(ev.get("item", ""))
            if spec:
                with self.det._lock:
                    self.det._due.pop(self.det.key(spec), None)

    def _reload_model(self) -> None:
        try:
            m = os.stat(self.cfg["model"]).st_mtime
        except OSError as exc:
            msg = f"plan model not readable: {exc}"
            if self.model_error != msg:
                self.model_error, self._dirty = msg, True
            return
        if m == self._model_mtime:
            return
        try:
            with open(self.cfg["model"], encoding="utf-8") as f:
                model = json.load(f)
            problems = check_model(model)
            if problems:
                raise ValueError("; ".join(problems[:5]))
            self.model, self.model_error, self._model_mtime = model, None, m
            self._dirty = True
        except (OSError, ValueError, KeyError) as exc:
            self.model_error = f"plan model rejected, still showing the previous one: {exc}"
            self._model_mtime = m
            self._dirty = True

    def _refresh_activity(self) -> None:
        try:
            out = {}
            for s in self.model.get("streams", []):
                acts = [D.git_activity(w) for w in s.get("worktrees", []) if os.path.isdir(w)]
                live = [a for a in acts if a.get("last_commit_ts")]
                latest = max(live, key=lambda a: a["last_commit_ts"]) if live else (acts[0] if acts else {"error": "no worktree yet"})
                out[s["id"]] = {**latest, "all": acts}
            if out != self.activity:
                self.activity = out
                self._dirty = True
        except Exception as exc:  # noqa: BLE001
            self.tick_errors.append(f"git activity: {exc}")
        finally:
            self._activity_at = time.time()
            self._activity_running = False

    def _backup(self) -> None:
        self._backup_at = time.time()
        src = self.cfg["events"]
        if not os.path.exists(src):
            return
        try:
            os.makedirs(self.cfg["backup_dir"], exist_ok=True)
            dst = os.path.join(self.cfg["backup_dir"], "EVENTS-" + dt.date.today().isoformat() + ".jsonl")
            if not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(src):
                tmp = dst + ".tmp"
                shutil.copyfile(src, tmp)
                os.replace(tmp, dst)
            for old in sorted(glob.glob(os.path.join(self.cfg["backup_dir"], "EVENTS-*.jsonl")))[:-14]:
                os.remove(old)
            self._backup_info = {"last": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "file": dst}
        except OSError as exc:
            self.tick_errors.append(f"backup failed: {exc}")

    def health(self) -> dict:
        errs = []
        for i in self.model.get("items", []):
            if i.get("detector"):
                r = self.det.get(i["detector"])
                if r and r.status == "error":
                    errs.append({"item": i["id"], "detail": r.detail})
        return {
            "server_started_at": self.started_at.isoformat(timespec="seconds"),
            "engine_tick_age_s": round(time.time() - self._last_tick, 1),
            "db_proxy": D.port_open(self.cfg["db_port"]),
            "db_credentials": bool(self.cfg["pgenv"] and os.path.exists(self.cfg["pgenv"])),
            "power": D.power_source(),
            "hold": os.path.exists(self.cfg["hold"]),
            "event_log": {"path": self.cfg["events"], "events": len(self.log.events), "malformed": self.log.malformed,
                          "exists": os.path.exists(self.cfg["events"])},
            "backup": self._backup_info,
            "model_error": self.model_error,
            "detector_errors": errs,
            "git_activity_age_s": round(time.time() - self._activity_at, 1) if self._activity_at else None,
            "tick_errors": list(self.tick_errors)[-3:],
        }

    def _rebuild(self) -> None:
        self._last_build = time.time()
        det_results = {}
        for i in self.model.get("items", []):
            if i.get("detector"):
                r = self.det.get(i["detector"])
                if r is not None:
                    det_results[i["id"]] = r.to_dict()
        snap = build_snapshot(self.model, list(self.log.events), det_results, {}, self.health(), self.activity)
        body = {k: v for k, v in snap.items() if k != "generated_at"}
        digest = hashlib.sha256(json.dumps(_strip_ages(body), sort_keys=True, default=str).encode()).hexdigest()
        with self.cond:
            if digest != self._digest:
                self.version += 1
                self._digest = digest
                self._persist(snap)
            snap["version"] = self.version
            self.snapshot = snap
            self.cond.notify_all()

    def _persist(self, snap: dict) -> None:
        path = self.cfg["snapshot"]
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            tmp = f"{path}.tmp.{os.getpid()}"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({**snap, "version": self.version}, f, ensure_ascii=False, default=str)
            os.replace(tmp, path)
        except OSError as exc:
            self.tick_errors.append(f"snapshot persist failed: {exc}")


def check_model(model: dict) -> list[str]:
    """Structural checks on the plan model. A rejected model never replaces the last good one."""
    problems = []
    ids = [i["id"] for i in model["items"]]
    dup = [x for x, n in collections.Counter(ids).items() if n > 1]
    if dup:
        problems.append(f"duplicate item ids: {dup[:5]}")
    idset = set(ids)
    tracks = {t["id"] for t in model["tracks"]}
    decs = {d["id"] for d in model.get("decisions", [])}
    streams = {s["id"] for s in model.get("streams", [])}
    for i in model["items"]:
        for d in i.get("depends_on", []):
            if d not in idset:
                problems.append(f"{i['id']} depends on unknown {d}")
        if i.get("track") not in tracks:
            problems.append(f"{i['id']} on unknown track {i.get('track')}")
        if i.get("done_by") == "decision" and i.get("decision") not in decs:
            problems.append(f"{i['id']} needs unknown decision {i.get('decision')}")
        for d in i.get("needs_decisions", []):
            if d not in decs:
                problems.append(f"{i['id']} needs unknown decision {d}")
        own = str(i.get("owner", ""))
        if own and own not in streams and own not in ("native", "steward"):
            problems.append(f"{i['id']} has unknown owner {own}")
    # cycle check
    deps = {i["id"]: i.get("depends_on", []) for i in model["items"]}
    state: dict[str, int] = {}

    def visit(n, path):
        if state.get(n) == 1:
            problems.append(f"dependency cycle: {' → '.join(path + [n])}")
            return
        if state.get(n) == 2:
            return
        state[n] = 1
        for d in deps.get(n, []):
            visit(d, path + [n])
        state[n] = 2

    for n in deps:
        visit(n, [])
    return problems


def _strip_ages(obj):
    if isinstance(obj, dict):
        return {k: _strip_ages(v) for k, v in obj.items()
                if not (k.endswith("_age_s") or k in ("elapsed_s", "age_s", "power", "liveness"))}
    if isinstance(obj, list):
        return [_strip_ages(v) for v in obj]
    return obj


def make_handler(engine: Engine):
    class Handler(BaseHTTPRequestHandler):
        server_version = "PravahaTracker/1"

        def log_message(self, fmt, *args):
            pass

        def _send(self, code: int, body: bytes, ctype: str):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, obj, code=200):
            return self._send(code, json.dumps(obj, ensure_ascii=False, default=str).encode(), "application/json; charset=utf-8")

        def do_GET(self):
            u = urlparse(self.path)
            path, q = u.path, parse_qs(u.query)
            if path in ("/", "/index.html"):
                return self._static("index.html")
            if path.startswith("/static/"):
                return self._static(path[len("/static/"):])
            with engine.cond:
                snap = engine.snapshot
            if path == "/api/state":
                return self._json(snap)
            if path == "/api/health":
                h = {"ok": engine.health()["engine_tick_age_s"] < 10, "version": engine.version, **engine.health()}
                return self._json(h, 200 if h["ok"] else 503)
            if path == "/api/next":
                sid = (q.get("stream") or [""])[0].upper()
                flat = [t for tr in snap.get("tracks", []) for t in tr["items"]]
                mine = [t for t in flat if not sid or t.get("owner") == sid]
                return self._json({"stream": sid, "version": snap.get("version"),
                                   "running": [t for t in mine if t["status"] in ("running", "review")],
                                   "ready": [t for t in mine if t["status"] == "ready"],
                                   "blocked": [t for t in mine if t["status"] in ("blocked", "failed", "parked", "conflict")]})
            if path == "/api/item":
                iid = (q.get("id") or [""])[0]
                flat = [t for tr in snap.get("tracks", []) for t in tr["items"]]
                it = next((t for t in flat if t["id"] == iid), None)
                return self._json(it or {"error": f"no item {iid}"}, 200 if it else 404)
            if path == "/events":
                return self._sse()
            return self._send(404, b"not found", "text/plain")

        def _static(self, rel: str):
            full = os.path.abspath(os.path.join(STATIC, rel))
            if not full.startswith(STATIC + os.sep) or not os.path.isfile(full):
                return self._send(404, b"not found", "text/plain")
            ctype = {"html": "text/html", "js": "application/javascript", "css": "text/css"}.get(full.rsplit(".", 1)[-1], "application/octet-stream")
            with open(full, "rb") as f:
                return self._send(200, f.read(), ctype + "; charset=utf-8")

        def _sse(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            sent, last_ping = -1, time.time()
            try:
                while not engine._stop.is_set():
                    with engine.cond:
                        if engine.version == sent:
                            engine.cond.wait(timeout=5)
                        snap, ver = engine.snapshot, engine.version
                    if ver != sent and snap:
                        data = json.dumps(snap, ensure_ascii=False, default=str)
                        self.wfile.write(f"id: {ver}\nevent: snapshot\ndata: {data}\n\n".encode())
                        self.wfile.flush()
                        sent, last_ping = ver, time.time()
                    elif time.time() - last_ping >= 5:
                        alive = json.dumps({"version": ver, "tick_age_s": round(time.time() - engine._last_tick, 1),
                                            "server_time": time.time()})
                        self.wfile.write(f"event: alive\ndata: {alive}\n\n".encode())
                        self.wfile.flush()
                        last_ping = time.time()
            except (BrokenPipeError, ConnectionResetError, OSError):
                return

    return Handler


class _QuietServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def handle_error(self, request, client_address):
        if isinstance(sys.exc_info()[1], (ConnectionResetError, BrokenPipeError, ConnectionAbortedError, TimeoutError)):
            return
        super().handle_error(request, client_address)


def serve(port: int, cfg: dict | None = None) -> tuple[ThreadingHTTPServer, Engine]:
    cfg = cfg or default_config()
    engine = Engine(cfg)
    engine.start()
    httpd = _QuietServer(("127.0.0.1", port), make_handler(engine))
    return httpd, engine


def main() -> None:
    ap = argparse.ArgumentParser(description="Pravāha real-time tracker")
    ap.add_argument("--port", type=int, default=int(os.environ.get("PRAVAHA_TRACKER_PORT", str(DEFAULT_PORT))))
    a = ap.parse_args()
    httpd, engine = serve(a.port)
    print(f"Pravāha tracker on http://127.0.0.1:{a.port}  (events: {engine.cfg['events']}; model: {engine.cfg['model']})", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        engine.stop()
        httpd.server_close()


if __name__ == "__main__":
    main()
