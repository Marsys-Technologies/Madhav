"""Build the dashboard snapshot: plan model + event log + detector results + metrics → one view.

Status rules (the earned-signal discipline, in order):
1. An item with a **detector**: the detector decides `done`. An event may set it running, in review,
   blocked or parked, but an event claiming `done` while the detector disagrees is shown as a
   conflict, never as done. A detector that cannot measure shows `unknown`, never done.
2. An item **done by decision**: done when the native's decision is recorded (decided or delegated).
3. An item **done by event**: done only by an event that carries evidence (enforced at write time).
4. Anything not started whose dependencies are all done is `ready`; otherwise `waiting`.
"""
from __future__ import annotations

import collections
import datetime as dt

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
    metrics: dict[str, dict] = {}
    for ev in events:
        k = ev.get("kind")
        if k == "item":
            items[ev["item"]].append(ev)
        elif k == "decision":
            decisions[ev["decision"]].append(ev)
        elif k == "heartbeat":
            heartbeats[ev.get("actor", "?")] = ev
        elif k == "metric" and ev.get("name"):
            metrics[ev["name"]] = ev
    return {"items": items, "decisions": decisions, "heartbeats": heartbeats, "metrics": metrics}


def decision_status(evs: list[dict]) -> tuple[str, dict | None]:
    if not evs:
        return "pending", None
    last = evs[-1]
    return last["state"], last


def item_status(item: dict, ix: dict, det_result: dict | None) -> dict:
    all_evs = ix["items"].get(item["id"], [])
    # A step event ("census done") advances only that step, never the whole item's status.
    evs = [e for e in all_evs if not e.get("step")]
    step_evs = [e for e in all_evs if e.get("step")]
    last = evs[-1] if evs else None
    if last is None and step_evs:
        last = dict(step_evs[-1], state="running")
    started = next((e["ts"] for e in all_evs if e["state"] in ("running", "review") or e.get("step")), None)
    out = {"status": "not_started", "source": "plan", "detail": "", "progress": None,
           "actor": last.get("actor") if last else None, "evidence": None,
           "started_at": started, "updated_at": last["ts"] if last else None, "checked_at": None}
    # steps (e.g. analysis: census → instance → briefs → designs)
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
            elif last and last["state"] == "done":
                out.update(status="conflict", detail=f"an event claims done; the detector says: {det_result['detail']}")
            elif last and last["state"] in ("running", "review", "blocked", "parked", "failed"):
                out["status"] = last["state"]
            elif ds in ("running", "blocked"):
                out["status"] = ds
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

    # done by event
    out["source"] = "event"
    if last:
        out["status"] = last["state"]
        out["detail"] = last.get("detail", "")
        if last["state"] == "done":
            out["evidence"] = last.get("evidence")
    return out


def build_snapshot(model: dict, events: list[dict], det_results: dict, metrics: dict,
                   health: dict, now: dt.datetime | None = None) -> dict:
    """Pure function: everything the dashboard shows. det_results maps item id → detector result dict."""
    now = now or dt.datetime.now(dt.timezone.utc)
    ix = index_events(events)
    items = {i["id"]: dict(i) for i in model["items"]}
    status = {iid: item_status(it, ix, det_results.get(iid)) for iid, it in items.items()}

    # readiness from dependencies
    for iid, it in items.items():
        s = status[iid]
        open_deps = [d for d in it.get("depends_on", []) if status.get(d, {}).get("status") != "done"]
        s["deps_open"] = open_deps
        if s["status"] == "not_started":
            s["status"] = "ready" if not open_deps else "waiting"

    tracks = []
    for tr in model["tracks"]:
        tis = []
        for iid, it in items.items():
            if it["track"] != tr["id"]:
                continue
            s = status[iid]
            tis.append({"id": iid, "title": it["title"], "lane": it.get("lane"), "gate": it.get("gate", False),
                        "depends_on": it.get("depends_on", []), **s,
                        "elapsed_s": _age_s(s["started_at"], now) if s["status"] in ("running", "review") else None})
        n = len(tis)
        done = sum(1 for t in tis if t["status"] == "done")
        partial = sum((t["progress"] or 0) for t in tis if t["status"] != "done")
        tracks.append({**tr, "items": tis, "done": done, "total": n,
                       "progress": (done + partial) / n if n else 0.0})

    flat = [t for tr in tracks for t in tr["items"]]
    counts = collections.Counter(t["status"] for t in flat)
    total = len(flat)
    done_w = counts.get("done", 0) + sum((t["progress"] or 0) for t in flat if t["status"] != "done")

    decisions = []
    needed_by = collections.defaultdict(list)
    for it in model["items"]:
        if it.get("decision"):
            needed_by[it["decision"]].append(it["id"])
    for d in model["decisions"]:
        st, dev = decision_status(ix["decisions"].get(d["id"], []))
        decisions.append({**d, "status": st, "detail": (dev or {}).get("detail", ""),
                          "updated_at": (dev or {}).get("ts"), "needed_by": needed_by.get(d["id"], [])})

    recent = [e for e in events[-40:]][::-1]
    last_ev = events[-1]["ts"] if events else None
    hb = {a: {"ts": e["ts"], "age_s": _age_s(e["ts"], now), "detail": e.get("detail", "")}
          for a, e in ix["heartbeats"].items()}
    done_24h = sum(1 for e in events if e.get("kind") == "item" and e["state"] == "done" and not e.get("step")
                   and _age_s(e["ts"], now) is not None and _age_s(e["ts"], now) <= 86400)

    return {
        "generated_at": now.isoformat(timespec="seconds"),
        "campaign": model.get("campaign"), "engine": model.get("engine"), "plan_ref": model.get("plan_ref"),
        "overall": {"total": total, "done": counts.get("done", 0), "running": counts.get("running", 0) + counts.get("review", 0),
                    "ready": counts.get("ready", 0), "waiting": counts.get("waiting", 0),
                    "blocked": counts.get("blocked", 0) + counts.get("failed", 0) + counts.get("parked", 0),
                    "unknown": counts.get("unknown", 0) + counts.get("conflict", 0),
                    "pct": round(100 * done_w / total, 1) if total else 0.0},
        "tracks": tracks,
        "now": [t for t in flat if t["status"] in ("running", "review")],
        "next": [t for t in flat if t["status"] == "ready"],
        "attention": [t for t in flat if t["status"] in ("blocked", "failed", "parked", "conflict", "unknown")],
        "done": sorted([t for t in flat if t["status"] == "done"], key=lambda t: t.get("updated_at") or t.get("checked_at") or "", reverse=True),
        "decisions": decisions,
        "metrics": {**metrics, "items_done_24h": done_24h,
                    "reported": {k: {"value": v.get("value"), "ts": v["ts"], "detail": v.get("detail", "")} for k, v in ix["metrics"].items()}},
        "activity": recent,
        "health": {**health, "heartbeats": hb, "last_event_at": last_ev, "last_event_age_s": _age_s(last_ev, now)},
    }
