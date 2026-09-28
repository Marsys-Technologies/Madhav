"""Suvarṇa tracker — a local, real-time dashboard server.

    python -m suvarna_tracker.server [--port 8765]      (run from platform/scripts/governance)

Real time: a background loop ticks every second. It tails the event log, reloads the plan model if
it changed, schedules detectors whose TTL expired, and — whenever anything changed — rebuilds the
snapshot and pushes it to every open browser over Server-Sent Events.

Resilience:
- binds to 127.0.0.1 only; read-only (no endpoint changes anything);
- every input is optional: a missing file, a dead database or a failing detector degrades that part
  of the view with an explicit error, never the whole page;
- the snapshot is also written atomically to $SUVARNA_HOME/run/snapshot.json on every change, so a
  restart shows the last state instantly and other tools can read it;
- the page shows its own freshness and switches to polling if the live stream drops;
- `run_tracker.sh` restarts the server if it ever exits.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import json
import os
import sys
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    __package__ = "suvarna_tracker"

from suvarna_tracker import detectors as D  # noqa: E402
from suvarna_tracker.events import EventLog  # noqa: E402
from suvarna_tracker.state import build_snapshot  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
STATIC = os.path.join(HERE, "static")
LAYER_NAMES = {"brahmagyan": "L0", "ganita": "L1", "bodha": "L2", "kala": "L3", "phala": "L4", "mimamsa": "L5"}


def default_config() -> dict:
    home = os.environ.get("SUVARNA_HOME", "/Users/Dev/suvarna")
    return {
        "home": home,
        "events": os.environ.get("SUVARNA_EVENTS", os.path.join(home, "run", "EVENTS.jsonl")),
        "snapshot": os.path.join(home, "run", "snapshot.json"),
        "hold": os.path.join(home, "run", "SUVARNA_HOLD"),
        "model": os.environ.get("SUVARNA_PLAN_MODEL",
                                os.path.join(REPO_ROOT, "00_ARCHITECTURE", "control", "suvarna", "plan_model.json")),
        "repo": os.environ.get("SUVARNA_REPO", REPO_ROOT),
        "nikasha_root": os.environ.get("NIKASHA_ROOT", "/Users/Dev/madhav-nikasha"),
        "pgenv": os.environ.get("SUVARNA_PGENV"),
        "db_port": int(os.environ.get("SUVARNA_DB_PORT", "5433")),
        "metrics_ttl": int(os.environ.get("SUVARNA_METRICS_TTL", "60")),
        "detectors_enabled": os.environ.get("SUVARNA_DETECTORS", "1") != "0",
    }


class Engine:
    """Owns all state; one background thread keeps it current."""

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.started_at = dt.datetime.now(dt.timezone.utc)
        self.log = EventLog(cfg["events"])
        self.det = D.Detectors(D.Config(repo=cfg["repo"], nikasha_root=cfg["nikasha_root"],
                                        pgenv=cfg["pgenv"], home=cfg["home"], db_port=cfg["db_port"]),
                               on_change=self._mark_dirty)
        self.model: dict = {"tracks": [], "items": [], "decisions": []}
        self.model_error: str | None = None
        self._model_mtime = None
        self.metrics: dict = {"status": "not yet measured"}
        self._metrics_at = 0.0
        self._metrics_running = False
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
        if self.cfg["detectors_enabled"]:
            self.det.poll([i["detector"] for i in self.model.get("items", []) if i.get("detector")])
        if time.time() - self._metrics_at > self.cfg["metrics_ttl"] and not self._metrics_running:
            self._metrics_running = True
            threading.Thread(target=self._refresh_metrics, name="metrics", daemon=True).start()
        # rebuild on change, and at least every 5 s so ages stay current
        if self._dirty or time.time() - self._last_build > 5:
            self._dirty = False
            self._rebuild()

    def _reload_model(self) -> None:
        try:
            m = os.stat(self.cfg["model"]).st_mtime
        except OSError as exc:
            if self.model_error != f"plan model not readable: {exc}":
                self.model_error = f"plan model not readable: {exc}"
                self._dirty = True  # surface errors as fast as any other change
            return
        if m == self._model_mtime:
            return
        try:
            with open(self.cfg["model"], encoding="utf-8") as f:
                model = json.load(f)
            ids = {i["id"] for i in model["items"]}
            dangling = [(i["id"], d) for i in model["items"] for d in i.get("depends_on", []) if d not in ids]
            if dangling:
                raise ValueError(f"dangling dependencies: {dangling[:5]}")
            self.model, self.model_error, self._model_mtime = model, None, m
            self._dirty = True
        except (OSError, ValueError, KeyError) as exc:
            # keep serving the last good model; show the error
            self.model_error = f"plan model rejected, still showing the previous one: {exc}"
            self._model_mtime = m
            self._dirty = True  # surface errors as fast as any other change

    def _refresh_metrics(self) -> None:
        out: dict = {"errors": [], "measured_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
        try:
            reg = D.parse_register(os.path.join(self.cfg["nikasha_root"], "00_ARCHITECTURE/briefs/nirmana/NIKASHA_CHANGE_REGISTER_v2_0.md"))
            out["register"] = D.register_counts(reg)
            out["register"]["malformed_rows"] = reg["malformed"]
        except Exception as exc:
            out["errors"].append(f"register: {exc}")
        layer_of: dict = {}
        try:
            levels = D.dag_levels(self.det)
            layer_of = {a: LAYER_NAMES.get(l, l) for a, l in D._dag_cache.get("layer", {}).items()}
            out["assets_by_layer"] = dict(sorted(collections.Counter(layer_of.values()).items()))
            out["assets_active"] = len(levels)
            out["dag_levels"] = (max(levels.values()) + 1) if levels else 0
        except Exception as exc:
            out["errors"].append(f"database: {exc}")
        try:
            ls = D.ledger_state(D.Config(repo=self.cfg["repo"], nikasha_root=self.cfg["nikasha_root"],
                                         pgenv=self.cfg["pgenv"], home=self.cfg["home"]))
            out["open_gaps"] = len(ls["open_gaps"])
            out["certifications"] = len(ls["certs"])
            if layer_of:
                out["open_gaps_by_layer"] = dict(sorted(collections.Counter(layer_of.get(g["asset"], "other") for g in ls["open_gaps"]).items()))
            elev = D.elevated_assets(D.Config(repo=self.cfg["repo"], nikasha_root=self.cfg["nikasha_root"],
                                              pgenv=self.cfg["pgenv"], home=self.cfg["home"]))
            out["elevated"] = len(elev)
            if layer_of:
                out["elevated_by_layer"] = {l: sum(1 for a in elev if layer_of.get(a) == l) for l in sorted(set(layer_of.values()))}
                levels = D._dag_cache.get("levels", {})
                by_level = collections.defaultdict(list)
                for a, lv in levels.items():
                    by_level[lv].append(a)
                out["levels_certified"] = sum(1 for lv, assets in by_level.items() if assets and all(a in elev for a in assets))
        except Exception as exc:
            out["errors"].append(f"ledgers: {exc}")
        self.metrics = out
        self._metrics_at = time.time()
        self._metrics_running = False
        self._dirty = True

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
            "power": D.power_source(),
            "hold": os.path.exists(self.cfg["hold"]),
            "event_log": {"path": self.cfg["events"], "events": len(self.log.events), "malformed": self.log.malformed,
                          "exists": os.path.exists(self.cfg["events"])},
            "model_error": self.model_error,
            "detector_errors": errs,
            "metrics_errors": self.metrics.get("errors", []),
            "metrics_age_s": round(time.time() - self._metrics_at, 1) if self._metrics_at else None,
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
        snap = build_snapshot(self.model, list(self.log.events), det_results, self.metrics, self.health())
        body = {k: v for k, v in snap.items() if k != "generated_at"}
        # ages change every second; exclude them from the change digest
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
            os.replace(tmp, path)  # atomic
        except OSError as exc:
            self.tick_errors.append(f"snapshot persist failed: {exc}")


def _strip_ages(obj):
    if isinstance(obj, dict):
        return {k: _strip_ages(v) for k, v in obj.items()
                if not (k.endswith("_age_s") or k in ("elapsed_s", "age_s", "power", "engine_tick_age_s", "metrics_age_s"))}
    if isinstance(obj, list):
        return [_strip_ages(v) for v in obj]
    return obj


def make_handler(engine: Engine):
    class Handler(BaseHTTPRequestHandler):
        server_version = "SuvarnaTracker/1"

        def log_message(self, fmt, *args):  # quiet
            pass

        def _send(self, code: int, body: bytes, ctype: str, extra: dict | None = None):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path in ("/", "/index.html"):
                return self._static("index.html")
            if path.startswith("/static/"):
                return self._static(path[len("/static/"):])
            if path == "/api/state":
                with engine.cond:
                    snap = engine.snapshot
                return self._send(200, json.dumps(snap, ensure_ascii=False, default=str).encode(), "application/json; charset=utf-8")
            if path == "/api/health":
                h = {"ok": engine.health()["engine_tick_age_s"] < 10, "version": engine.version, **engine.health()}
                return self._send(200 if h["ok"] else 503, json.dumps(h, default=str).encode(), "application/json")
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
            sent = -1
            last_ping = time.time()
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
                        sent = ver
                        last_ping = time.time()
                    elif time.time() - last_ping >= 5:
                        # A visible heartbeat (not an SSE comment, which browsers never surface), so the
                        # page can tell "quiet but healthy" from "stuck": it carries the engine's tick age.
                        alive = json.dumps({"version": ver, "tick_age_s": round(time.time() - engine._last_tick, 1),
                                            "server_time": time.time()})
                        self.wfile.write(f"event: alive\ndata: {alive}\n\n".encode())
                        self.wfile.flush()
                        last_ping = time.time()
            except (BrokenPipeError, ConnectionResetError, OSError):
                return

    return Handler


class _QuietServer(ThreadingHTTPServer):
    """A browser closing a tab mid-request is normal, not an error: keep it out of the log so real errors stand out."""

    def handle_error(self, request, client_address):
        import sys
        if isinstance(sys.exc_info()[1], (ConnectionResetError, BrokenPipeError, ConnectionAbortedError, TimeoutError)):
            return
        super().handle_error(request, client_address)


def serve(port: int, cfg: dict | None = None) -> tuple[ThreadingHTTPServer, Engine]:
    cfg = cfg or default_config()
    engine = Engine(cfg)
    engine.start()
    httpd = _QuietServer(("127.0.0.1", port), make_handler(engine))
    httpd.daemon_threads = True
    return httpd, engine


def main() -> None:
    ap = argparse.ArgumentParser(description="Suvarṇa real-time tracker")
    ap.add_argument("--port", type=int, default=int(os.environ.get("SUVARNA_TRACKER_PORT", "8765")))
    a = ap.parse_args()
    httpd, engine = serve(a.port)
    print(f"Suvarṇa tracker on http://127.0.0.1:{a.port}  (events: {engine.cfg['events']})", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        engine.stop()
        httpd.server_close()


if __name__ == "__main__":
    main()
