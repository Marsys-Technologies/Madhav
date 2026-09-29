"""Build the dashboard snapshot: plan model + event log + detector results + metrics → one view.

Status rules (the earned-signal discipline, in order):
1. An item with a **detector**: the detector decides `done`. An event may set it running, in review,
   blocked or parked, but an event claiming `done` while the detector disagrees is shown as a
   conflict, never as done. A detector that cannot measure shows `unknown`, never done.
2. An item **done by decision**: driven by the authoritative decisions log (`decisions.py`
   DECISIONS.jsonl), not by decision events (Fix 2 — review: any actor's `decided`/`delegated`
   *event* used to turn a native gate done). `decided` in the log → done; `delegated` in the log →
   not done, `waiting` with detail naming who it's delegated to; otherwise a `requested` *event*
   shows `running` "awaiting the native"; otherwise waiting/ready as usual. A decision *event*
   claiming `decided`/`delegated` that disagrees with the log (or that the log has no record of) is
   surfaced as a `conflict` on that decision's row in the snapshot's `decisions` table, never used to
   drive the gate. Callers that don't pass a decisions log (`decisions=None`) keep the old,
   event-driven behaviour for backward compatibility.
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
    """Status from decision *events* only (the workflow signal, not the authoritative record)."""
    if not evs:
        return "pending", None
    last = evs[-1]
    return last["state"], last


def decision_log_status(dec_id: str, decisions: dict | None) -> tuple[str, dict | None]:
    """Status from the authoritative decisions log (decisions.load_decisions' return shape:
    {'latest': {id: record}, 'malformed': N}), or ('none', None) if there's no record — or no log
    was supplied at all (decisions is None)."""
    if not decisions:
        return "none", None
    rec = decisions.get("latest", {}).get(dec_id)
    if not rec:
        return "none", None
    return rec.get("state", "none"), rec


# CODE-14 (S2, review pass 2): narrowed to the one role authorized to write the decisions log going
# forward — only Strategic Suvarṇa, native present (charter §2, §7.5, P14); the Steward carries
# answers, never records a ruling. A `decided`/`delegated` decision *event* from "steward" now
# surfaces the same warning as any other unexpected actor.
ALLOWED_DECISION_WRITERS = {"strategic-suvarna"}


def decision_event_warnings(events: list[dict]) -> list[str]:
    """Decision events from an actor other than the one role authorized to write the decisions log
    (Fix 2; narrowed by CODE-14) — these events never drive a gate, but are worth surfacing as a
    health warning since an unexpected actor emitting one usually means a misconfigured writer
    somewhere."""
    out = []
    for e in events:
        if (e.get("kind") == "decision" and e.get("state") in ("decided", "delegated")
                and e.get("actor") not in ALLOWED_DECISION_WRITERS):
            out.append(f"{e.get('actor')} emitted a {e['state']} decision event for "
                       f"{e.get('decision')} (ts {e.get('ts')})")
    return out


def item_status(item: dict, ix: dict, det_result: dict | None, decisions: dict | None = None) -> dict:
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
                out["soft"] = True  # the detector sees activity, but no role has claimed the item
        return out

    if item.get("done_by") == "decision":
        dec_id = item.get("decision", "")
        out["source"] = "decision:" + (dec_id or "?")
        log_state, log_rec = decision_log_status(dec_id, decisions)
        if decisions is not None and log_state == "decided":
            evidence = f"{log_rec.get('detail', '')} — {log_rec.get('source', '')}"
            out.update(status="done", detail=log_rec.get("detail", ""), evidence=evidence,
                       updated_at=log_rec.get("ts"))
            return out
        if decisions is not None and log_state == "delegated":
            delegated_to = log_rec.get("delegated_to") or "?"
            out.update(status="waiting", detail=f"delegated to {delegated_to}; not yet decided",
                       updated_at=log_rec.get("ts"))
            return out
        st, dev = decision_status(ix["decisions"].get(dec_id, []))
        if decisions is None and st in ("decided", "delegated"):
            # Backward-compatible path: no authoritative log supplied — fall back to the old,
            # event-driven behaviour so existing callers keep working unchanged.
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
                   health: dict, now: dt.datetime | None = None, decisions: dict | None = None) -> dict:
    """Pure function: everything the dashboard shows. det_results maps item id → detector result dict.

    `decisions` is the authoritative decisions log as returned by `decisions.load_decisions()`
    ({'latest': {id: record}, 'malformed': N}), or None to keep the old, event-only behaviour
    (backward compatible for callers/tests that don't pass one — Fix 2)."""
    now = now or dt.datetime.now(dt.timezone.utc)
    ix = index_events(events)
    items = {i["id"]: dict(i) for i in model["items"]}
    status = {iid: item_status(it, ix, det_results.get(iid), decisions) for iid, it in items.items()}

    # readiness from dependencies
    for iid, it in items.items():
        s = status[iid]
        open_deps = [d for d in it.get("depends_on", []) if status.get(d, {}).get("status") != "done"]
        s["deps_open"] = open_deps
        # Activity a detector sees (e.g. a PR already open) does not make a gated item "running":
        # while its dependencies are open, it is waiting on them.
        if s.pop("soft", False) and open_deps:
            s["status"] = "waiting"
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

    decisions_rows = []
    needed_by = collections.defaultdict(list)
    for it in model["items"]:
        if it.get("decision"):
            needed_by[it["decision"]].append(it["id"])
    for d in model["decisions"]:
        ev_state, ev = decision_status(ix["decisions"].get(d["id"], []))
        if decisions is not None:
            log_state, log_rec = decision_log_status(d["id"], decisions)
            if log_state != "none":
                row_status, row_detail, row_updated = log_state, log_rec.get("detail", ""), log_rec.get("ts")
            else:
                row_status, row_detail, row_updated = ev_state, (ev or {}).get("detail", ""), (ev or {}).get("ts")
            row = {**d, "status": row_status, "detail": row_detail, "updated_at": row_updated,
                   "needed_by": needed_by.get(d["id"], [])}
            # A decision *event* claiming decided/delegated that the log doesn't corroborate (missing
            # or disagreeing) is a conflict — surfaced, never used to drive the gate (Fix 2).
            if ev_state in ("decided", "delegated") and (log_state == "none" or log_state != ev_state):
                row["status"] = "conflict"
                row["conflict"] = {"event": ev_state, "log": log_state}
            decisions_rows.append(row)
        else:
            decisions_rows.append({**d, "status": ev_state, "detail": (ev or {}).get("detail", ""),
                                   "updated_at": (ev or {}).get("ts"), "needed_by": needed_by.get(d["id"], [])})

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
        "decisions": decisions_rows,
        "metrics": {**metrics, "items_done_24h": done_24h,
                    "reported": {k: {"value": v.get("value"), "ts": v["ts"], "detail": v.get("detail", "")} for k, v in ix["metrics"].items()}},
        "activity": recent,
        "health": {**health, "heartbeats": hb, "last_event_at": last_ev, "last_event_age_s": _age_s(last_ev, now),
                   "decision_event_warnings": decision_event_warnings(events)},
    }
