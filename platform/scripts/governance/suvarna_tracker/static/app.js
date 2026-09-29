/* Suvarṇa tracker — client. Live over Server-Sent Events; falls back to polling if the stream drops.
   Every figure shows its freshness; nothing is shown as current once it is stale. */
(() => {
  "use strict";
  const STALE_AFTER_S = 20;       // no update for this long → "stale" banner
  const POLL_EVERY_MS = 5000;     // fallback polling interval
  let snap = null, lastMsg = 0, lastAlive = 0, tickAge = 0, es = null, pollTimer = null, mode = "connecting";

  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const LABEL = { done: "done", running: "running", review: "in review", ready: "ready", waiting: "waiting",
    blocked: "blocked", parked: "parked", failed: "failed", unknown: "unmeasured", conflict: "conflict" };

  function ago(iso) {
    if (!iso) return "—";
    const s = Math.max(0, (Date.now() - Date.parse(iso)) / 1000);
    if (s < 60) return `${Math.round(s)}s ago`;
    if (s < 3600) return `${Math.round(s / 60)}m ago`;
    if (s < 86400) return `${Math.round(s / 3600)}h ago`;
    return `${Math.round(s / 86400)}d ago`;
  }
  function dur(s) {
    if (s == null) return "";
    if (s < 60) return `${Math.round(s)}s`;
    if (s < 3600) return `${Math.round(s / 60)}m`;
    return `${(s / 3600).toFixed(1)}h`;
  }

  // ---- connection -------------------------------------------------------------------------
  function connect() {
    try { es && es.close(); } catch (_) {}
    es = new EventSource("/events");
    es.addEventListener("snapshot", (e) => { try { accept(JSON.parse(e.data), "live"); } catch (_) {} });
    // The server sends "alive" every 5 s even when nothing changes, so a quiet campaign reads as healthy.
    es.addEventListener("alive", (e) => {
      try { const a = JSON.parse(e.data); lastAlive = Date.now(); tickAge = a.tick_age_s || 0; mode = "live"; } catch (_) {}
      paintLive();
    });
    es.onerror = () => { mode = "reconnecting"; startPolling(); paintLive(); };
    es.onopen = () => { mode = "live"; stopPolling(); paintLive(); };
  }
  function startPolling() {
    if (pollTimer) return;
    pollTimer = setInterval(async () => {
      try {
        const r = await fetch("/api/state", { cache: "no-store" });
        if (r.ok) accept(await r.json(), "polling");
        else mode = "down";
      } catch (_) { mode = "down"; }
      paintLive();
    }, POLL_EVERY_MS);
  }
  function stopPolling() { if (pollTimer) { clearInterval(pollTimer); pollTimer = null; } }
  function accept(s, via) {
    if (!s || !s.tracks) return;
    snap = s; lastMsg = lastAlive = Date.now(); tickAge = 0; if (via === "live") mode = "live"; else if (mode !== "live") mode = "polling";
    render();
  }

  function paintLive() {
    const el = $("live"), t = $("live-text");
    const since = lastAlive ? (Date.now() - lastAlive) / 1000 : Infinity;      // last contact with the server
    const changed = snap?.generated_at ? ago(snap.generated_at) : "—";          // last time any value (incl. a re-check) moved
    let cls = "live-connecting", text = "Connecting…";
    if (mode === "down") { cls = "live-down"; text = `Server unreachable — last data ${lastMsg ? ago(new Date(lastMsg).toISOString()) : "never"}`; }
    else if (since > STALE_AFTER_S) { cls = "live-stale"; text = `Stale — no contact for ${Math.round(since)}s`; }
    else if (tickAge > 10) { cls = "live-stale"; text = `Server engine stuck — last tick ${Math.round(tickAge)}s ago`; }
    else if (mode === "live") { cls = "live-ok"; text = `Live · data refreshed ${changed} · v${snap?.version ?? "–"}`; }
    else if (mode === "polling" || mode === "reconnecting") { cls = "live-stale"; text = `Polling (stream reconnecting) · ${Math.round(since)}s ago`; }
    el.className = "live " + cls; t.textContent = text;
  }

  // ---- rendering --------------------------------------------------------------------------
  function card(it) {
    const st = it.status;
    const prog = it.progress != null && st !== "done" ? `<div class="p"><div style="width:${Math.round(it.progress * 100)}%"></div></div>` : "";
    const steps = it.steps ? `<div class="steps">${it.steps.map((s) => `<span class="${s.done ? "on" : ""}">${esc(s.name)}</span>`).join("")}</div>` : "";
    const when = (st === "running" || st === "review") && it.elapsed_s != null ? `for ${dur(it.elapsed_s)}` : it.checked_at ? `checked ${ago(it.checked_at)}` : it.updated_at ? ago(it.updated_at) : "";
    const tip = [it.detail, `source: ${it.source}`, it.deps_open?.length ? `waiting on: ${it.deps_open.join(", ")}` : "", it.evidence ? `evidence: ${it.evidence}` : ""].filter(Boolean).join("\n");
    return `<div class="card st-${st} ${it.gate ? "gate" : ""}" title="${esc(tip)}">
      <div class="t">${esc(it.title)}</div>
      <div class="s"><span class="badge">${esc(LABEL[st] || st)}</span><span>${esc(it.id)}</span><span>${esc(when)}</span></div>${steps}${prog}</div>`;
  }

  function renderPlan() {
    $("plan").innerHTML = snap.tracks.map((tr) => {
      const lanes = {};
      tr.items.forEach((it) => { const k = it.lane || ""; (lanes[k] = lanes[k] || []).push(it); });
      const seq = tr.mode === "sequential";
      const laneHtml = Object.entries(lanes).map(([k, its]) =>
        `<div class="lane">${k ? `<div class="lane-h">${esc(k)}</div>` : ""}${its.map(card).join("")}</div>`).join("");
      return `<div class="track"><div class="track-h"><h3>${esc(tr.title)}</h3>
        <span class="mode">${esc(tr.mode)}</span>
        <span class="tprog"><span class="bar"><div style="width:${Math.round(tr.progress * 100)}%;height:100%;background:var(--done)"></div></span>${tr.done}/${tr.total}</span></div>
        <div class="sub" style="margin-bottom:8px">${esc(tr.plain || "")}</div>
        <div class="lanes ${seq ? "seq" : ""}">${laneHtml}</div></div>`;
    }).join("");
  }

  function rows(el, items, empty, meta) {
    $(el).innerHTML = items.length ? items.map((it) =>
      `<div class="row"><span class="id">${esc(it.id)}</span><span class="t">${esc(it.title)}</span><span class="meta">${meta(it)}</span></div>`).join("")
      : `<div class="empty">${esc(empty)}</div>`;
  }

  function renderWhere() {
    rows("now", snap.now, "Nothing running.", (it) => [esc(LABEL[it.status]), it.actor ? esc(it.actor) : "", it.elapsed_s != null ? `for ${dur(it.elapsed_s)}` : "", esc(it.detail || "")].filter(Boolean).join(" · "));
    rows("next", snap.next.slice(0, 12), "Nothing ready — everything is waiting on something.", (it) => esc(it.source));
    const pend = snap.decisions.filter((d) => d.status === "requested").map((d) => ({ id: d.id, title: d.title, status: "requested", detail: `awaiting you · recommendation: ${d.recommendation}` }));
    rows("attention", [...pend, ...snap.attention], "Nothing needs attention.", (it) => `${esc(LABEL[it.status] || it.status)}${it.detail ? " · " + esc(it.detail) : ""}`);
    rows("done", snap.done.slice(0, 20), "Nothing completed yet.", (it) => `${esc(it.evidence || it.detail || "")}`);
  }

  function renderCounts() {
    const o = snap.overall;
    $("pct").textContent = o.pct.toFixed(1);
    $("pct-bar").style.width = `${o.pct}%`;
    const chip = (k, v) => `<span class="chip st-${k}"><b>${v}</b>${esc(LABEL[k] || k)}</span>`;
    $("counts").innerHTML = [chip("done", o.done), chip("running", o.running), chip("ready", o.ready), chip("waiting", o.waiting),
      chip("blocked", o.blocked), chip("unknown", o.unknown), `<span class="chip"><b>${o.total}</b>items in plan</span>`].join("");
  }

  function renderHealth() {
    const h = snap.health || {};
    const hb = h.heartbeats?.conductor;
    const items = [
      [hb ? (hb.age_s < 600 ? "ok" : "bad") : "warn", `Conductor: ${hb ? "heartbeat " + ago(hb.ts) : "not running yet"}`],
      [h.db_proxy ? "ok" : "bad", `Database proxy: ${h.db_proxy ? "up" : "down"}`],
      [h.power === "ac" ? "ok" : "warn", `Power: ${h.power || "?"}`],
      [h.hold ? "warn" : "ok", `Hold switch: ${h.hold ? "ON — no new work" : "off"}`],
      [h.event_log?.malformed ? "warn" : (h.event_log?.exists ? "ok" : "warn"), `Event log: ${h.event_log?.events ?? 0} events${h.event_log?.malformed ? `, ${h.event_log.malformed} malformed` : ""}`],
      [h.last_event_age_s == null ? "warn" : "ok", `Last event: ${ago(h.last_event_at)}`],
      [(h.detector_errors?.length || 0) ? "warn" : "ok", `Checkers: ${(h.detector_errors?.length || 0) ? h.detector_errors.length + " unmeasured" : "all measuring"}`],
      [(h.metrics_errors?.length || 0) ? "warn" : "ok", `Metrics: ${h.metrics_age_s != null ? "measured " + dur(h.metrics_age_s) + " ago" : "pending"}`],
    ];
    if (h.model_error) items.push(["bad", h.model_error]);
    if (h.restored_from_disk) items.push(["warn", "Showing last saved state while starting"]);
    $("health").innerHTML = items.map(([c, t]) => `<span class="hitem ${c}" title="${esc(t)}">${esc(t)}</span>`).join("");
  }

  function renderMetrics() {
    const m = snap.metrics || {};
    const kpi = (v, t, tip) => `<div class="kpi"${tip ? ` title="${esc(tip)}"` : ""}><b>${v ?? "—"}</b><span>${esc(t)}</span></div>`;
    const reg = m.register || {};
    const open = reg.by_state?.OPEN;
    let html = `<div class="kpis">${kpi(m.elevated_proxy != null ? `${m.elevated_proxy}/${m.assets_active ?? "?"}` : null, "elevated (proxy)", m.elevated_definition)}
      ${kpi(m.certifications, "certification records")}${kpi(m.open_gaps, "open gap rows")}
      ${kpi(m.levels_certified != null ? `${m.levels_certified}/${m.dag_levels ?? "?"}` : null, "dependency levels certified")}
      ${kpi(open, "register rows open")}${kpi(m.items_done_24h, "plan items done, 24h")}</div>`;
    if (m.assets_by_layer) {
      html += `<h3 class="sub">Elevated per layer</h3>` + Object.entries(m.assets_by_layer).map(([l, n]) => {
        const e = m.elevated_by_layer?.[l] ?? 0; const g = m.open_gaps_by_layer?.[l] ?? 0;
        return `<div class="hbar"><span>${esc(l)}</span><span class="bar"><div style="width:${n ? (100 * e / n) : 0}%;height:100%;background:var(--done)"></div></span><span>${e}/${n} · ${g} gaps</span></div>`;
      }).join("");
    }
    if (reg.open_by_severity) {
      html += `<h3 class="sub">Open register rows by severity</h3><table>${Object.entries(reg.open_by_severity).sort().map(([k, v]) => `<tr><td>${esc(k)}</td><td class="num">${v}</td></tr>`).join("")}</table>`;
    }
    const rep = m.reported || {};
    if (Object.keys(rep).length) {
      html += `<h3 class="sub">Reported measurements</h3><table>${Object.entries(rep).map(([k, v]) => `<tr><td>${esc(k)}</td><td>${esc(v.value)}</td><td class="sub">${ago(v.ts)}</td></tr>`).join("")}</table>`;
    }
    if (m.errors?.length) html += `<div class="hitem bad" style="margin-top:8px">${esc(m.errors.join(" · "))}</div>`;
    html += `<div class="sub" style="margin-top:6px">measured ${ago(m.measured_at)}</div>`;
    $("metrics").innerHTML = html;
  }

  function renderDecisions() {
    const order = { requested: 0, pending: 1, delegated: 2, decided: 3 };
    const ds = [...snap.decisions].sort((a, b) => (order[a.status] ?? 9) - (order[b.status] ?? 9));
    $("decisions").innerHTML = `<table><tr><th>ID</th><th>Decision</th><th>Status</th><th>Recommendation</th></tr>${ds.map((d) =>
      `<tr><td class="sub">${esc(d.id)}</td><td>${esc(d.title)}${d.detail ? `<div class="sub">${esc(d.detail)}</div>` : ""}</td>
       <td><span class="badge ${d.status === "decided" || d.status === "delegated" ? "st-done" : d.status === "requested" ? "st-ready" : "st-waiting"}" style="border:1px solid">${esc(d.status)}</span></td>
       <td class="sub">${esc(d.recommendation)}</td></tr>`).join("")}</table>`;
  }

  function renderActivity() {
    const f = (e) => {
      const what = e.kind === "item" ? `${e.item} → ${e.state}${e.step ? ` (${e.step})` : ""}` : e.kind === "decision" ? `${e.decision} → ${e.state}` : e.kind === "metric" ? `${e.name} = ${e.value}` : e.kind;
      return `<div class="ev"><time>${esc((e.ts || "").replace("T", " ").slice(5, 16))}</time><b>${esc(e.actor)}</b> · ${esc(what)}${e.detail ? ` — <span class="sub">${esc(e.detail)}</span>` : ""}</div>`;
    };
    $("activity").innerHTML = snap.activity.length ? snap.activity.map(f).join("") : `<div class="empty">No events yet.</div>`;
  }

  function render() {
    try {
      renderCounts(); renderHealth(); renderWhere(); renderPlan(); renderMetrics(); renderDecisions(); renderActivity();
      $("foot").textContent = `Snapshot v${snap.version ?? "–"} · built ${snap.generated_at} · plan: ${snap.plan_ref}`;
    } catch (err) {
      $("foot").textContent = "Render error: " + err;
    }
    paintLive();
  }

  setInterval(paintLive, 1000);                              // freshness ticks every second
  setInterval(() => { if (snap) { renderWhere(); } }, 15000); // elapsed times stay current
  // This page never uses a service worker. Remove any a previous app on this port left behind,
  // so it can never again serve that app's cached pages here.
  try {
    navigator.serviceWorker?.getRegistrations().then((rs) => rs.forEach((r) => r.unregister())).catch(() => {});
    window.caches?.keys().then((ks) => ks.forEach((k) => caches.delete(k))).catch(() => {});
  } catch (_) {}
  fetch("/api/state", { cache: "no-store" }).then((r) => r.json()).then((s) => accept(s, "polling")).catch(() => {});
  connect();
})();
