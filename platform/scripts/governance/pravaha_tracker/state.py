"""Build the dashboard snapshot: plan model + event log + detector results + stream activity → one view.

Status rules (earned-signal discipline, CLAUDE.md §N.8), in order:
1. An item with a **detector**: the detector decides `done`. An event may set it running, in review,
   blocked or parked, but an event claiming `done` while the detector disagrees is a *conflict*,
   never done. A detector that cannot measure shows `unknown`, never done.
2. An item **done by decision**: done when the native's decision is recorded (decided/delegated).
3. An item **done by join**: done when every dependency is done — a join is a fact about the plan,
   so no event can claim it.
4. An item **done by event**: done only by an event carrying evidence (enforced at write time).
5. Anything not started whose dependencies are all done is `ready`; otherwise `waiting`.

Stream liveness (Pravāha addition): each stream's last heartbeat, last event and last commit are
shown side by side. A stream with work `running` and no heartbeat for `stale_after_s` is *stale*
(amber); past `dead_after_s` it is *silent* (red). A stream with nothing running is *idle*, which is
not an alarm.
"""
from __future__ import annotations

import collections
import datetime as dt

from .events import actor_stream

STATUS_ORDER = ["done", "running", "review", "ready", "waiting", "blocked", "parked", "failed", "unknown", "conflict"]


def _age_s(ts: str | None, now: dt.datetime) -> float | None:
    if not ts:
        return None
    try:
        t = dt.datetime.fromisoformat(ts)
    except ValueError:
        return None
    if t.tzinfo is None:
        t = t.replace(tzinfo=dt.timezone.utc)
    return max(0.0, (now - t).total_seconds())


def index_events(events: list[dict]) -> dict:
    items: dict[str, list] = collections.defaultdict(list)
    decisions: dict[str, list] = collections.defaultdict(list)
    heartbeats: dict[str, dict] = {}
    last_by_actor: dict[str, dict] = {}
    metrics: dict[str, dict] = {}
    notes: list[dict] = []
    for ev in events:
        k = ev.get("kind")
        last_by_actor[ev.get("actor", "?")] = ev
        if k == "item":
            items[ev["item"]].append(ev)
        elif k == "decision":
            decisions[ev["decision"]].append(ev)
        elif k == "heartbeat":
            heartbeats[ev.get("actor", "?")] = ev
        elif k == "metric" and ev.get("name"):
            metrics[ev["name"]] = ev
        elif k == "note":
            notes.append(ev)
    return {"items": items, "decisions": decisions, "heartbeats": heartbeats, "metrics": metrics,
            "last_by_actor": last_by_actor, "notes": notes}


def decision_status(evs: list[dict]) -> tuple[str, dict | None]:
    if not evs:
        return "pending", None
    last = evs[-1]
    return last["state"], last


def item_status(item: dict, ix: dict, det_result: dict | None) -> dict:
    all_evs = ix["items"].get(item["id"], [])
    evs = [e for e in all_evs if not e.get("step")]
    step_evs = [e for e in all_evs if e.get("step")]
    last = evs[-1] if evs else None
    if last is None and step_evs:
        last = dict(step_evs[-1], state="running")
    started = next((e["ts"] for e in all_evs if e["state"] in ("running", "review") or e.get("step")), None)
    out = {"status": "not_started", "source": "plan", "detail": "", "progress": None,
           "actor": last.get("actor") if last else None, "evidence": None,
           "started_at": started, "updated_at": last["ts"] if last else None, "checked_at": None}
    if item.get("steps"):
        done_steps = {e.get("step") for e in step_evs if e["state"] == "done"}
        out["steps"] = [{"name": s, "done": s in done_steps} for s in item["steps"]]
        out["progress"] = len(done_steps & set(item["steps"])) / len(item["steps"])
    if last and last.get("progress") is not None:
        out["progress"] = last["progress"]

    if item.get("detector"):
        out["source"] = "detector:" + item["detector"]["type"]
        if det_result is None:
            out.update(status="unknown", detail="not yet measured")
            if last and last["state"] in ("running", "review", "blocked", "parked", "failed"):
                out.update(status=last["state"], detail=last.get("detail", "") + " (detector not yet measured)")
        else:
            out["checked_at"] = det_result["checked_at"]
            out["detail"] = det_result["detail"]
            if det_result.get("progress") is not None:
                out["progress"] = det_result["progress"]
            ds = det_result["status"]
            if ds == "done":
                out["status"] = "done"
                out["evidence"] = det_result["detail"]
            elif ds == "error":
                out["status"] = "unknown"
                if last and last["state"] in ("running", "review", "blocked", "parked", "failed"):
                    out.update(status=last["state"], detail=f"{last.get('detail', '')} · detector: {det_result['detail']}")
            elif last and last["state"] == "done":
                out.update(status="conflict", detail=f"an event claims done; the detector says: {det_result['detail']}")
            elif last and last["state"] in ("running", "review", "blocked", "parked", "failed"):
                out["status"] = last["state"]
                if last.get("detail"):
                    out["detail"] = f"{last['detail']} · {det_result['detail']}"
            elif ds in ("running", "blocked"):
                out["status"] = ds
                out["soft"] = True
        return out

    if item.get("done_by") == "decision":
        st, dev = decision_status(ix["decisions"].get(item.get("decision", ""), []))
        out["source"] = "decision:" + item.get("decision", "?")
        if st in ("decided", "delegated"):
            out.update(status="done", detail=dev.get("detail", ""), evidence=dev.get("detail"), updated_at=dev["ts"])
        elif st == "requested":
            out.update(status="running", detail="awaiting the native", updated_at=dev["ts"])
        elif last:
            out["status"] = last["state"]
        return out

    if item.get("done_by") == "join":
        out["source"] = "join"
        return out  # resolved from dependencies in build_snapshot

    out["source"] = "event"
    if last:
        out["status"] = last["state"]
        out["detail"] = last.get("detail", "")
        if last["state"] == "done":
            out["evidence"] = last.get("evidence")
    return out


def _stream_view(stream: dict, flat: list[dict], ix: dict, activity: dict, now: dt.datetime) -> dict:
    sid = stream["id"]
    actor_keys = [a for a in ix["last_by_actor"] if actor_stream(a) == sid]
    hb = [ix["heartbeats"][a] for a in actor_keys if a in ix["heartbeats"]]
    hb_last = max(hb, key=lambda e: e["ts"]) if hb else None
    ev_last = max((ix["last_by_actor"][a] for a in actor_keys), key=lambda e: e["ts"], default=None)
    mine = [t for t in flat if t.get("owner") == sid]
    running = [t for t in mine if t["status"] in ("running", "review")]
    ready = [t for t in mine if t["status"] == "ready"]
    blocked = [t for t in mine if t["status"] in ("blocked", "failed", "parked", "conflict")]
    hb_age = _age_s(hb_last["ts"], now) if hb_last else None
    stale_after, dead_after = stream.get("stale_after_s", 900), stream.get("dead_after_s", 2700)
    if running:
        if hb_age is None:
            live = "silent"
        elif hb_age > dead_after:
            live = "silent"
        elif hb_age > stale_after:
            live = "stale"
        else:
            live = "active"
    else:
        live = "idle" if (hb_age is None or hb_age > stale_after) else "active"
    git = activity.get(sid) or {}
    done = sum(1 for t in mine if t["status"] == "done")
    return {**stream, "liveness": live,
            "heartbeat": {"ts": hb_last["ts"], "age_s": hb_age, "detail": hb_last.get("detail", "")} if hb_last else None,
            "last_event": {"ts": ev_last["ts"], "age_s": _age_s(ev_last["ts"], now),
                           "what": ev_last.get("item") or ev_last.get("decision") or ev_last.get("kind"),
                           "state": ev_last.get("state"), "detail": ev_last.get("detail", "")} if ev_last else None,
            "git": git, "running": running, "ready": ready[:8], "blocked": blocked,
            "done": done, "total": len(mine), "progress": (done + sum((t["progress"] or 0) for t in mine if t["status"] != "done")) / len(mine) if mine else 0.0}


def build_snapshot(model: dict, events: list[dict], det_results: dict, metrics: dict,
                   health: dict, activity: dict | None = None, now: dt.datetime | None = None) -> dict:
    """Pure function: everything the dashboard shows. det_results maps item id → detector result dict;
    activity maps stream id → git activity dict."""
    now = now or dt.datetime.now(dt.timezone.utc)
    activity = activity or {}
    ix = index_events(events)
    items = {i["id"]: dict(i) for i in model["items"]}
    status = {iid: item_status(it, ix, det_results.get(iid)) for iid, it in items.items()}

    # dependencies → readiness; joins resolve here (repeat until stable: joins may depend on joins)
    for _ in range(len(items) + 1):
        changed = False
        for iid, it in items.items():
            s = status[iid]
            open_deps = [d for d in it.get("depends_on", []) if status.get(d, {}).get("status") != "done"]
            s["deps_open"] = open_deps
            if it.get("done_by") == "join":
                new = "done" if not open_deps else "waiting"
                if s["status"] != new:
                    s["status"] = new
                    s["evidence"] = "all dependencies done" if new == "done" else None
                    changed = True
        if not changed:
            break
    for iid, it in items.items():
        s = status[iid]
        if s.pop("soft", False) and s["deps_open"]:
            s["status"] = "waiting"
        # An unmeasured detector on an item that cannot start yet is not an alarm: show it as waiting,
        # keep "unmeasured" in the detail, and raise it only once the item becomes startable.
        if s["status"] == "unknown" and s["deps_open"] and not ix["items"].get(iid):
            s["status"] = "waiting"
            s["detail"] = f"unmeasured until startable — {s.get('detail', '')}"
        if s["status"] == "not_started":
            s["status"] = "ready" if not s["deps_open"] else "waiting"

    tracks = []
    for tr in model["tracks"]:
        tis = []
        for iid, it in items.items():
            if it["track"] != tr["id"]:
                continue
            s = status[iid]
            tis.append({"id": iid, "title": it["title"], "lane": it.get("lane"), "gate": it.get("gate", False),
                        "owner": it.get("owner"), "depends_on": it.get("depends_on", []),
                        "cross_stream": it.get("cross_stream", False), **s,
                        "elapsed_s": _age_s(s["started_at"], now) if s["status"] in ("running", "review") else None})
        n = len(tis)
        done = sum(1 for t in tis if t["status"] == "done")
        partial = sum((t["progress"] or 0) for t in tis if t["status"] != "done")
        tracks.append({**tr, "items": tis, "done": done, "total": n, "progress": (done + partial) / n if n else 0.0})

    flat = [t for tr in tracks for t in tr["items"]]
    counts = collections.Counter(t["status"] for t in flat)
    total = len(flat)
    done_w = counts.get("done", 0) + sum((t["progress"] or 0) for t in flat if t["status"] != "done")

    decisions = []
    # a decision gates the work that depends on its decision item (not the decision item itself)
    needed_by = collections.defaultdict(list)
    dec_item = {it["id"]: it["decision"] for it in model["items"] if it.get("done_by") == "decision" and it.get("decision")}
    for it in model["items"]:
        for dep in it.get("depends_on", []):
            if dep in dec_item:
                needed_by[dec_item[dep]].append(it["id"])
        for d in it.get("needs_decisions", []):
            needed_by[d].append(it["id"])
    for d in model["decisions"]:
        st, dev = decision_status(ix["decisions"].get(d["id"], []))
        decisions.append({**d, "status": st, "detail": (dev or {}).get("detail", ""),
                          "updated_at": (dev or {}).get("ts"), "needed_by": needed_by.get(d["id"], [])})

    streams = [_stream_view(s, flat, ix, activity, now) for s in model.get("streams", [])]
    phases = []
    for ph in model.get("phases", []):
        its = [t for t in flat if t.get("lane") in ph.get("lanes", [])]
        if its:
            d = sum(1 for t in its if t["status"] == "done")
            phases.append({**ph, "done": d, "total": len(its), "pct": round(100 * d / len(its), 1)})

    recent = [e for e in events[-60:]][::-1]
    last_ev = events[-1]["ts"] if events else None
    hb = {a: {"ts": e["ts"], "age_s": _age_s(e["ts"], now), "detail": e.get("detail", "")} for a, e in ix["heartbeats"].items()}
    done_24h = sum(1 for e in events if e.get("kind") == "item" and e["state"] == "done" and not e.get("step")
                   and (_age_s(e["ts"], now) or 1e9) <= 86400)
    rank = {"requested": 0, "pending": 1}
    # a decision is due once its decision item is startable (its inputs exist) or a stream has requested it;
    # a decision whose inputs do not exist yet is listed as "not yet due", never as waiting on the native
    dec_item_status = {it["decision"]: status.get(it["id"], {}).get("status") for it in model["items"]
                       if it.get("done_by") == "decision" and it.get("decision")}
    for d in decisions:
        d["due"] = d["status"] == "requested" or dec_item_status.get(d["id"]) not in ("waiting",)
    pending_native = sorted([d for d in decisions if d["status"] in ("requested", "pending") and d["due"]],
                            key=lambda d: (rank[d["status"]], -sum(1 for x in d["needed_by"] if status.get(x, {}).get("status") in ("ready", "waiting"))))

    return {
        "generated_at": now.isoformat(timespec="seconds"),
        "campaign": model.get("campaign"), "subtitle": model.get("subtitle"), "plan_ref": model.get("plan_ref"),
        "overall": {"total": total, "done": counts.get("done", 0),
                    "running": counts.get("running", 0) + counts.get("review", 0),
                    "ready": counts.get("ready", 0), "waiting": counts.get("waiting", 0),
                    "blocked": counts.get("blocked", 0) + counts.get("failed", 0) + counts.get("parked", 0),
                    "unknown": counts.get("unknown", 0) + counts.get("conflict", 0),
                    "pct": round(100 * done_w / total, 1) if total else 0.0},
        "streams": streams,
        "phases": phases,
        "tracks": tracks,
        "now": [t for t in flat if t["status"] in ("running", "review")],
        "next": [t for t in flat if t["status"] == "ready"],
        "attention": [t for t in flat if t["status"] in ("blocked", "failed", "parked", "conflict", "unknown")],
        "done": sorted([t for t in flat if t["status"] == "done"],
                       key=lambda t: t.get("updated_at") or t.get("checked_at") or "", reverse=True),
        "decisions": decisions,
        "native_queue": [{"id": d["id"], "title": d["title"], "status": d["status"],
                          "recommendation": d.get("recommendation", ""), "needed_by": d["needed_by"]} for d in pending_native],
        "metrics": {**metrics, "items_done_24h": done_24h,
                    "reported": {k: {"value": v.get("value"), "ts": v["ts"], "detail": v.get("detail", ""),
                                     "actor": v.get("actor")} for k, v in ix["metrics"].items()}},
        "activity": recent,
        "health": {**health, "heartbeats": hb, "last_event_at": last_ev, "last_event_age_s": _age_s(last_ev, now)},
    }
