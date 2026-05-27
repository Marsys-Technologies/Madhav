// server.mjs — standalone HTTP + SSE server for the program tracker.
// No npm deps. Run: `node server.mjs` or `npm start` from this directory.
// PORT env override; defaults to 8787 per BRIEF_0t.

import { createServer } from "node:http";
import { readFileSync, existsSync, watch } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

import { collect, sourcesFingerprint, REPO_ROOT, TRACKER_DIR } from "./collect.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PUBLIC_DIR = join(__dirname, "public");
const PORT = parseInt(process.env.PORT || "8787", 10);
const POLL_MS = 2000; // collect interval; SSE pushes only on change.

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js":   "application/javascript; charset=utf-8",
  ".css":  "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg":  "image/svg+xml",
};

let lastFingerprint = "";
let lastStatus = null;
const sseClients = new Set();

async function refreshStatus(reason = "tick") {
  try {
    const status = await collect();
    lastStatus = status;
    const fp = sourcesFingerprint() + ":" + (status.main_head || "");
    if (fp !== lastFingerprint) {
      lastFingerprint = fp;
      pushToClients(status, reason);
    }
  } catch (e) {
    process.stderr.write(`[tracker] collect error: ${e && e.message || e}\n`);
  }
}

function pushToClients(status, reason) {
  const payload = `event: status\ndata: ${JSON.stringify(status)}\n\n`;
  for (const res of sseClients) {
    try { res.write(payload); } catch {}
  }
  if (process.env.TRACKER_VERBOSE) {
    process.stderr.write(`[tracker] sse push (${reason}) → ${sseClients.size} client(s)\n`);
  }
}

function serveFile(req, res, path) {
  if (!existsSync(path)) { res.writeHead(404); return res.end("not found"); }
  const ext = path.slice(path.lastIndexOf("."));
  res.writeHead(200, { "Content-Type": MIME[ext] || "application/octet-stream", "Cache-Control": "no-store" });
  res.end(readFileSync(path));
}

const server = createServer(async (req, res) => {
  // CORS — useful when the UI is opened directly from disk during dev.
  res.setHeader("Access-Control-Allow-Origin", "*");

  const url = new URL(req.url, `http://localhost:${PORT}`);
  if (req.method === "GET" && (url.pathname === "/" || url.pathname === "/index.html")) {
    return serveFile(req, res, join(PUBLIC_DIR, "index.html"));
  }
  if (req.method === "GET" && url.pathname === "/status.json") {
    const status = lastStatus || await collect();
    res.writeHead(200, { "Content-Type": MIME[".json"], "Cache-Control": "no-store" });
    return res.end(JSON.stringify(status));
  }
  if (req.method === "GET" && url.pathname === "/events") {
    res.writeHead(200, {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      "Connection": "keep-alive",
      "X-Accel-Buffering": "no",
    });
    res.write(": tracker stream open\n\n");
    sseClients.add(res);
    if (lastStatus) res.write(`event: status\ndata: ${JSON.stringify(lastStatus)}\n\n`);
    const ping = setInterval(() => { try { res.write(": ping\n\n"); } catch {} }, 15000);
    req.on("close", () => { clearInterval(ping); sseClients.delete(res); });
    return;
  }
  if (req.method === "GET" && url.pathname === "/healthz") {
    res.writeHead(200, { "Content-Type": "text/plain" });
    return res.end("ok");
  }
  if (req.method === "GET" && url.pathname.startsWith("/public/")) {
    return serveFile(req, res, join(__dirname, url.pathname));
  }
  res.writeHead(404);
  res.end("not found");
});

server.on("listening", async () => {
  await refreshStatus("boot");
  const addr = server.address();
  process.stderr.write(`[tracker] listening on http://localhost:${addr.port}\n`);
});

// Re-collect every POLL_MS (cheap; ~5–20 ms per call) and emit SSE on change.
setInterval(() => refreshStatus("tick"), POLL_MS);

// Best-effort file watchers — push immediately when a source file changes.
try {
  const watchPaths = [
    join(REPO_ROOT, "00_ARCHITECTURE/CONDUCTOR/modernization"),
    join(TRACKER_DIR, ".state"),
  ];
  for (const p of watchPaths) {
    if (!existsSync(p)) continue;
    watch(p, { recursive: true }, () => refreshStatus("watch"));
  }
} catch {}

server.listen(PORT, "127.0.0.1");

function shutdown() {
  for (const res of sseClients) { try { res.end(); } catch {} }
  server.close(() => process.exit(0));
}
process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
