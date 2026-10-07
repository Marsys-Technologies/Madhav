/* Pravāha tracker — client. Live over Server-Sent Events; falls back to polling if the stream drops.
   Every figure shows its freshness; nothing is shown as current once it is stale. */
(() => {
  "use strict";
  const STALE_AFTER_S = 20;
  const POLL_EVERY_MS = 5000;
  let snap = null, lastMsg = 0, lastAlive = 0, tickAge = 0, es = null, pollTimer = null, mode = "connecting";

  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const LABEL = { done: "done", running: "running", review: "in review", ready: "ready", waiting: "waiting",
    blocked: "blocked", parked: "parked", failed: "failed", unknown: "unmeasured", conflict: "conflict" };
  const LIVE = { active: ["ok", "active"], idle: ["idle", "idle — nothing running"], stale: ["warn", "stale — no heartbeat"], silent: ["bad", "silent — work running, no heartbeat"] };

  function ago(iso) {
    if (!iso) return "—";
    const s = Math.max(0, (Date.now() - (typeof iso === "number" ? iso * 1000 : Date.parse(iso))) / 1000);
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
        if (r.ok) accept(await r.json(), "polling"); else mode = "down";
      } catch (_) { mode = "down"; }
      paintLive();
    }, POLL_EVERY_MS);
  }
  function stopPolling() { if (pollTimer) { clearInterval(pollTimer); pollTimer = null; } }
  function accept(s, via) {
    if (!s || !s.tracks) return;
    snap = s; lastMsg = lastAlive = Date.now(); tickAge = 0;
    if (via === "live") mode = "live"; else if (mode !== "live") mode = "polling";
    render();
  }
  function paintLive() {
    const el = $("live"), t = $("live-text");
    const since = lastAlive ? (Date.now() - lastAlive) / 1000 : Infinity;
    const changed = snap?.generated_at ? ago(snap.generated_at) : "—";
    let cls = "live-connecting", text = "Connecting…";
    if (mode === "down") { cls = "live-down"; text = `Server unreachable — last data ${lastMsg ? ago(new Date(lastMsg).toISOString()) : "never"}`; }
    else if (since > STALE_AFTER_S) { cls = "live-stale"; text = `Stale — no contact for ${Math.round(since)}s`; }
    else if (tickAge > 10) { cls = "live-stale"; text = `Server engine stuck — last tick ${Math.round(tickAge)}s ago`; }
    else if (mode === "live") { cls = "live-ok"; text = `Live · refreshed ${changed} · v${snap?.version ?? "–"}`; }
    else if (mode === "polling" || mode === "reconnecting") { cls = "live-stale"; text = `Polling (stream reconnecting) · ${Math.round(since)}s ago`; }
    el.className = "live " + cls; t.textContent = text;
  }

  // ---- rendering --------------------------------------------------------------------------
  function card(it) {
    const st = it.status;
    const prog = it.progress != null && st !== "done" ? `<div class="p"><div style="width:${Math.round(it.progress * 100)}%"></div></div>` : "";
    const steps = it.steps ? `<div class="steps">${it.steps.map((s) => `<span class="${s.done ? "on" : ""}">${esc(s.name)}</span>`).join("")}</div>` : "";
    const when = (st === "running" || st === "review") && it.elapsed_s != null ? `for ${dur(it.elapsed_s)}` : it.checked_at ? `checked ${ago(it.checked_at)}` : it.updated_at ? ago(it.updated_at) : "";
    const tip = [it.detail, `owner: ${it.owner || "—"}`, `source: ${it.source}`, it.depends_on?.length ? `depends on: ${it.depends_on.join(", ")}` : "",
      it.deps_open?.length ? `waiting on: ${it.deps_open.join(", ")}` : "", it.evidence ? `evidence: ${it.evidence}` : ""].filter(Boolean).join("\n");
    return `<div class="card st-${st} ${it.gate ? "gate" : ""}" title="${esc(tip)}">
      <div class="t">${it.cross_stream ? '<span class="xs" title="waits on the other stream">⇄</span> ' : ""}${esc(it.title)}</div>
      <div class="s"><span class="badge">${esc(LABEL[st] || st)}</span><span>${esc(it.id)}</span><span>${esc(when)}</span></div>${steps}${prog}</div>`;
  }

  function mini(it) {
    return `<div class="mini st-${it.status}" title="${esc(it.detail || "")}"><span class="id">${esc(it.id)}</span> ${esc(it.title)}${it.elapsed_s != null ? ` <span class="sub">· ${dur(it.elapsed_s)}</span>` : ""}</div>`;
  }

  function renderStreams() {
    $("streams").innerHTML = (snap.streams || []).map((s) => {
      const [cls, txt] = LIVE[s.liveness] || ["warn", s.liveness];
      const hb = s.heartbeat ? `heartbeat ${ago(s.heartbeat.ts)}${s.heartbeat.detail ? " — " + esc(s.heartbeat.detail) : ""}` : "no heartbeat yet";
      const le = s.last_event ? `last event ${ago(s.last_event.ts)}: ${esc(s.last_event.what)}${s.last_event.state ? " → " + esc(s.last_event.state) : ""}` : "no events yet";
      const g = s.git || {};
      const gl = g.error ? `<span class="sub">git: ${esc(g.error)}</span>` : g.subject ? `last commit ${ago(g.last_commit_ts)} on <code>${esc(g.branch)}</code>: ${esc(g.subject)}${g.dirty_files ? ` · ${g.dirty_files} uncommitted` : ""}` : "";
      const pct = Math.round((s.progress || 0) * 100);
      return `<div class="panel stream">
        <div class="stream-h"><h2>Stream ${esc(s.id)} — ${esc(s.name)}</h2><span class="pill ${cls}">${esc(txt)}</span></div>
        <div class="sub">${esc(s.plain || "")}</div>
        <div class="sprog"><span class="bar"><div style="width:${pct}%"></div></span><span>${s.done}/${s.total} · ${pct}%</span></div>
        <div class="sline">${hb}</div><div class="sline">${le}</div><div class="sline">${gl}</div>
        <div class="scols">
          <div><h3>Running</h3>${s.running.length ? s.running.map(mini).join("") : '<div class="empty">nothing</div>'}</div>
          <div><h3>Ready</h3>${s.ready.length ? s.ready.map(mini).join("") : '<div class="empty">nothing ready</div>'}</div>
          <div><h3>Blocked</h3>${s.blocked.length ? s.blocked.map(mini).join("") : '<div class="empty">none</div>'}</div>
        </div></div>`;
    }).join("");
  }

  function renderNative() {
    const q = snap.native_queue || [];
    $("native-panel").style.display = q.length ? "" : "none";
    const req = q.filter((d) => d.status === "requested").length;
    $("native-count").textContent = `${req} requested · ${q.length - req} not yet requested`;
    $("native").innerHTML = `<table class="compact">${q.map((d) => `<tr class="${d.status === "requested" ? "req" : ""}">
      <td class="sub">${esc(d.id)}</td><td>${esc(d.title)}</td>
      <td><span class="badge ${d.status === "requested" ? "st-ready" : "st-waiting"}">${esc(d.status)}</span></td>
      <td class="sub">→ ${esc(d.recommendation)}</td><td class="sub">gates ${esc(d.needed_by.join(", ") || "—")}</td></tr>`).join("")}</table>`;
  }

  function renderPhases() {
    $("phases").innerHTML = (snap.phases || []).map((p) =>
      `<div class="phase"><div class="ph-h"><b>${esc(p.title)}</b><span class="sub">${p.done}/${p.total}</span></div>
       <span class="bar"><div style="width:${p.pct}%"></div></span><div class="sub">${esc(p.plain || "")}</div></div>`).join("");
  }

  function renderPlan() {
    $("plan").innerHTML = snap.tracks.map((tr) => {
      const lanes = {};
      tr.items.forEach((it) => { const k = it.lane || ""; (lanes[k] = lanes[k] || []).push(it); });
      const laneHtml = Object.entries(lanes).map(([k, its]) =>
        `<div class="lane">${k ? `<div class="lane-h">${esc(k)}</div>` : ""}${its.map(card).join("")}</div>`).join("");
      return `<div class="track"><div class="track-h"><h3>${esc(tr.title)}</h3><span class="mode">${esc(tr.mode)}</span>
        <span class="tprog"><span class="bar"><div style="width:${Math.round(tr.progress * 100)}%"></div></span>${tr.done}/${tr.total}</span></div>
        <div class="sub" style="margin-bottom:8px">${esc(tr.plain || "")}</div>
        <div class="lanes ${tr.mode === "sequential" ? "seq" : ""}">${laneHtml}</div></div>`;
    }).join("");
  }

  function rows(el, items, empty, meta) {
    $(el).innerHTML = items.length ? items.map((it) =>
      `<div class="row"><span class="id">${esc(it.id)}</span><span class="t">${esc(it.title)}</span><span class="meta">${meta(it)}</span></div>`).join("")
      : `<div class="empty">${esc(empty)}</div>`;
  }
  function renderWhere() {
    rows("now", snap.now, "Nothing running.", (it) => [esc(LABEL[it.status]), it.owner ? "Stream " + esc(it.owner) : "", it.elapsed_s != null ? `for ${dur(it.elapsed_s)}` : "", esc(it.detail || "")].filter(Boolean).join(" · "));
    rows("next", snap.next.slice(0, 14), "Nothing ready — everything is waiting on something.", (it) => `${it.owner ? "Stream " + esc(it.owner) + " · " : ""}${esc(it.source)}`);
    rows("attention", snap.attention, "Nothing needs attention.", (it) => `${esc(LABEL[it.status] || it.status)}${it.detail ? " · " + esc(it.detail) : ""}`);
    rows("done", snap.done.slice(0, 25), "Nothing completed yet.", (it) => `${esc(it.evidence || it.detail || "")}`);
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
    const items = [
      [h.event_log?.malformed ? "warn" : (h.event_log?.exists ? "ok" : "warn"), `Event log: ${h.event_log?.events ?? 0} events${h.event_log?.malformed ? `, ${h.event_log.malformed} malformed` : ""}`],
      [h.last_event_age_s == null ? "warn" : "ok", `Last event: ${ago(h.last_event_at)}`],
      [(h.detector_errors?.length || 0) ? "warn" : "ok", `Checkers: ${(h.detector_errors?.length || 0) ? h.detector_errors.length + " unmeasured" : "all measuring"}`],
      [h.db_credentials ? (h.db_proxy ? "ok" : "warn") : "warn", `Database checks: ${h.db_credentials ? (h.db_proxy ? "proxy up" : "proxy down") : "no read-only credential set (D-T1)"}`],
      [h.backup?.last ? "ok" : "warn", `Backup: ${h.backup?.last ? ago(h.backup.last) : "pending"}`],
      [h.power === "ac" ? "ok" : "warn", `Power: ${h.power || "?"}`],
      [h.hold ? "warn" : "ok", `Hold switch: ${h.hold ? "ON — no new work" : "off"}`],
    ];
    if (h.model_error) items.push(["bad", h.model_error]);
    if (h.restored_from_disk) items.push(["warn", "Showing last saved state while starting"]);
    (h.tick_errors || []).forEach((e) => items.push(["bad", "engine: " + e.slice(0, 120)]));
    $("health").innerHTML = items.map(([c, t]) => `<span class="hitem ${c}" title="${esc(t)}">${esc(t)}</span>`).join("");
  }

  function renderMetrics() {
    const m = snap.metrics || {};
    const rep = m.reported || {};
    let html = `<div class="kpis"><div class="kpi"><b>${m.items_done_24h ?? 0}</b><span>items done, last 24h</span></div>
      <div class="kpi"><b>${snap.decisions.filter((d) => d.status === "decided" || d.status === "delegated").length}/${snap.decisions.length}</b><span>decisions made</span></div></div>`;
    html += Object.keys(rep).length ? `<table>${Object.entries(rep).map(([k, v]) =>
      `<tr><td>${esc(k)}</td><td>${esc(v.value)}</td><td class="sub">${esc(v.actor || "")} · ${ago(v.ts)}</td></tr>`).join("")}</table>`
      : `<div class="empty">No measurements reported yet (benchmarks, root counts, retrodiction scores land here).</div>`;
    $("metrics").innerHTML = html;
  }

  function renderDecisions() {
    const order = { requested: 0, pending: 1, delegated: 2, decided: 3 };
    const ds = [...snap.decisions].sort((a, b) => (order[a.status] ?? 9) - (order[b.status] ?? 9));
    $("decisions").innerHTML = `<table><tr><th>ID</th><th>Decision</th><th>Status</th><th>Recommendation</th></tr>${ds.map((d) =>
      `<tr><td class="sub">${esc(d.id)}</td><td>${esc(d.title)}${d.detail ? `<div class="sub">${esc(d.detail)}</div>` : ""}</td>
       <td><span class="badge ${d.status === "decided" || d.status === "delegated" ? "st-done" : d.status === "requested" ? "st-ready" : "st-waiting"}">${esc(d.status === "pending" && !d.due ? "not yet due" : d.status)}</span></td>
       <td class="sub">${esc(d.recommendation)}</td></tr>`).join("")}</table>`;
  }

  function renderActivity() {
    const f = (e) => {
      const what = e.kind === "item" ? `${e.item} → ${e.state}${e.step ? ` (${e.step})` : ""}` : e.kind === "decision" ? `${e.decision} → ${e.state}` : e.kind === "metric" ? `${e.name} = ${e.value}` : e.kind === "message" ? `✉ → ${e.to}${e.ref ? ` [${e.ref}]` : ""}` : e.kind === "ack" ? `✓ ack ${e.msg_id}` : e.kind;
      return `<div class="ev"><time>${esc((e.ts || "").replace("T", " ").slice(5, 16))}</time><b>${esc(e.actor)}</b> · ${esc(what)}${e.detail ? ` — <span class="sub">${esc(e.detail)}</span>` : ""}</div>`;
    };
    $("activity").innerHTML = snap.activity.length ? snap.activity.map(f).join("") : `<div class="empty">No events yet.</div>`;
  }

  function render() {
    try {
      if (snap.subtitle) $("subtitle").textContent = snap.subtitle;
      renderCounts(); renderHealth(); renderNative(); renderStreams(); renderPhases(); renderWhere(); renderPlan(); renderMetrics(); renderDecisions(); renderActivity();
      $("foot").textContent = `Snapshot v${snap.version ?? "–"} · built ${snap.generated_at} · plan: ${snap.plan_ref}`;
    } catch (err) {
      $("foot").textContent = "Render error: " + err;
    }
    paintLive();
  }

  setInterval(paintLive, 1000);
  setInterval(() => { if (snap) { renderStreams(); renderWhere(); } }, 15000);
  try {
    navigator.serviceWorker?.getRegistrations().then((rs) => rs.forEach((r) => r.unregister())).catch(() => {});
  } catch (_) {}
  fetch("/api/state", { cache: "no-store" }).then((r) => r.json()).then((s) => accept(s, "polling")).catch(() => {});
  connect();
})();
