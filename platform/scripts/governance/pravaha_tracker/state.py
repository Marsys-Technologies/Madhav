"""Build the dashboard snapshot: plan model + event log + detector results + stream activity → one view.

Status rules (earned-signal discipline, CLAUDE.md §N.8), in order. The legacy
Pravāha rules below remain unchanged. A model with control_plane.guarded_completion
instead requires a guarded done event; a matching detector is evidence only:
1. An item with a **detector**: the detector decides `done`. An event may set it running, in review,
   blocked or parked, but an event claiming `done` while the detector disagrees is a *conflict*,
   never done. A detector that cannot measure shows `unknown`, never done.
2. An item **done by decision**: done when the native's final decision is recorded
   (decided/delegated) and every declared dependency is complete.
3. An item **done by join**: done when every dependency is done — a join is a fact about the plan,
   so no event can claim it.
4. An item **done by event**: done only by an event carrying evidence (enforced at write time).
5. Anything not started whose dependencies are all done is `ready`; otherwise `waiting`.
6. SR-BOLD-07: a declared code item is also `done` when its PR is merged and contained in a successful deploy of
   main (merged_deployed.py) — the PR's merged review is its acceptance; no verdict event is written or needed.
   Operation items still close from executor receipts and decisions from the ledger.

A7 D-46 (guarded models): a code/artifact item may complete while its dependencies are still open (see
completion.D46_KINDS). Such a `done` row is *implemented*; it carries `activation_pending` (its open gates) and is
*activated* only once that list is empty. `overall` reports implemented/total and activated/total; `close_ready`
needs every applicable item both implemented and activated.

Stream liveness (Pravāha addition): each stream's last heartbeat, last event and last commit are
shown side by side. A stream with work `running` and no heartbeat for `stale_after_s` is *stale*
(amber); past `dead_after_s` it is *silent* (red). A stream with nothing running is *idle*, which is
not an alarm.
"""
from __future__ import annotations

import collections
import datetime as dt
import json
import os
from pathlib import Path

from . import merged_deployed
from .events import actor_stream

# A live install runs a copy of this file outside the repository; PRAVAHA_REPO names the repository it reads
# (the same variable cli.py and server.py already honour). A9-NB-01.
REPO_ROOT = Path(os.environ.get("PRAVAHA_REPO") or Path(__file__).resolve().parents[4])

DECLARATION_KEYS = ("completion_kind", "producer", "reviewer_rule", "step_evidence")
STATUS_ORDER = ["done", "not_applicable", "running", "review", "ready", "waiting", "blocked", "parked", "failed", "unknown", "conflict"]


# A7 D-46: only code/artifact items may complete (be *implemented*) while a gate is open.
D46_KINDS = ("code", "artifact")


def _terminal(item: dict) -> set[str]:
    return ({"done", "not_applicable"}
            if item.get("accepts_not_applicable_dependencies") is True else {"done"})


def open_dependencies(item: dict, rows: dict[str, dict], *, relaxed: bool = False) -> list[str]:
    """Ordered completion gates; merge/acceptance evidence never closes a dependency.

    A dependency that is implemented but not yet activated (it carries `activation_pending`) satisfies only a
    `relaxed` (D-46 code/artifact) dependant; operation, packet, decision and join items keep strict ordered
    completion (SR-A4-01) and still wait for the upstream to be activated.
    """
    terminal = _terminal(item)
    return [dep for dep in item.get("depends_on", [])
            if rows.get(dep, {}).get("status") not in terminal
            or (not relaxed and rows[dep].get("activation_pending"))]


def pending_gates(item: dict, rows: dict[str, dict]) -> list[str]:
    """Transitive D-46 activation gates of `item`: its non-terminal dependencies plus the gates its implemented
    dependencies are themselves still waiting on. Empty exactly when everything upstream is activated."""
    terminal, gates = _terminal(item), []
    for dep in item.get("depends_on", []):
        row = rows.get(dep, {})
        for gate in ([dep] if row.get("status") not in terminal else row.get("activation_pending") or []):
            if gate not in gates:
                gates.append(gate)
    return gates


def is_relaxed(model: dict, item: dict, row: dict) -> bool:
    """D-46 applies to `item` (declared code/artifact; an undeclared model: its recorded completion's type)."""
    if isinstance(model.get("control_plane", {}).get("declarations"), dict):
        return item.get("completion_kind") in D46_KINDS
    return row.get("completion_type") in D46_KINDS


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


def item_status(item: dict, ix: dict, det_result: dict | None, *, guarded: bool = False,
                decision_outcomes: dict | None = None, derived: dict | None = None) -> dict:
    all_evs = ix["items"].get(item["id"], [])
    evs = [e for e in all_evs if not e.get("step")]
    step_evs = [e for e in all_evs if e.get("step")]
    last = evs[-1] if evs else None
    completed = next((e for e in reversed(evs) if e.get("state") == "done" and
                      e.get("guarded") is True), None) if guarded else None
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
        # In KĀLA-YANTRA the detector supplies evidence, not the terminal transition.
        # The completion command validates the conjunction before writing this event.
        # Once recorded, completion remains durable if an external detector flaps.
        if completed:
            out.update(status="done", source="guarded:event", evidence=completed.get("evidence"),
                       detail=completed.get("detail", ""), updated_at=completed["ts"])
            out["completion_type"] = (completed.get("completion") or {}).get("type")
            if det_result is not None:
                out["checked_at"] = det_result["checked_at"]
                if det_result["status"] != "done":
                    out["detector_warning"] = det_result["detail"]
            return out
        if derived and item.get("completion_kind") == "code":
            # SR-BOLD-07: a code item whose PR is merged and contained in a successful main deploy is done. The
            # PR's merged review is the acceptance, so no verdict event stands behind this (merged_deployed.py).
            out.update(status="done", source=merged_deployed.SOURCE, evidence=derived["evidence"],
                       detail=derived["detail"], completion_type="code", merged_pr=derived["pr"],
                       deploy_run_id=derived["deploy_run_id"])
            if det_result is not None:
                out["checked_at"] = det_result["checked_at"]
            return out
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
            if ds == "done" and not guarded:
                out["status"] = "done"
                out["evidence"] = det_result["detail"]
            elif ds == "done" and guarded:
                if last and last["state"] == "done":
                    out.update(status="conflict", detail="unguarded done event; independent acceptance missing")
                else:
                    out["detail"] = f"detector matched; guarded completion pending: {det_result['detail']}"
                if last and last["state"] in ("running", "review", "blocked", "parked", "failed"):
                    out["status"] = last["state"]
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
            outcome = dev.get("outcome")
            if decision_outcomes and outcome in decision_outcomes.get("open", []):
                out.update(status="waiting", detail=dev.get("detail", ""), updated_at=dev["ts"])
            else:
                out.update(status="done", detail=dev.get("detail", ""), evidence=dev.get("detail"),
                           updated_at=dev["ts"])
            if outcome:
                out["outcome"] = outcome
        elif st == "requested":
            out.update(status="running", detail="awaiting the native", updated_at=dev["ts"])
        elif last:
            out["status"] = last["state"]
        return out

    if item.get("done_by") == "join":
        out["source"] = "join"
        return out  # resolved from dependencies in build_snapshot

    out["source"] = "event"
    if completed:
        out.update(status="done", source="guarded:event", evidence=completed.get("evidence"),
                   detail=completed.get("detail", ""), updated_at=completed["ts"])
        out["completion_type"] = (completed.get("completion") or {}).get("type")
        return out
    if last:
        out["status"] = ("conflict" if guarded and last["state"] == "done" and
                         last.get("guarded") is not True else last["state"])
        out["detail"] = last.get("detail", "")
        if out["status"] == "conflict":
            out["detail"] = "unguarded done event; independent acceptance missing"
        elif last["state"] == "done":
            out["evidence"] = last.get("evidence")
    return out


def _stream_view(stream: dict, flat: list[dict], ix: dict, activity: dict, now: dt.datetime) -> dict:
    sid = stream["id"]
    actor_keys = [a for a in ix["last_by_actor"] if actor_stream(a) == sid]
    hb = [ix["heartbeats"][a] for a in actor_keys if a in ix["heartbeats"]]
    hb_last = max(hb, key=lambda e: e["ts"]) if hb else None
    ev_last = max((ix["last_by_actor"][a] for a in actor_keys), key=lambda e: e["ts"], default=None)
    mine = [t for t in flat if t.get("owner") == sid]
    running = [t for t in mine if t["display_status"] in ("running", "review")]
    ready = [t for t in mine if t["display_status"] == "ready"]
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
            "built_waiting_on_gate": [t for t in mine if t["built_waiting_on_gate"]],
            "done": done, "total": len(mine), "progress": (done + sum((t["progress"] or 0) for t in mine if t["status"] != "done")) / len(mine) if mine else 0.0}


def load_closure(model: dict, root: Path | None = None) -> dict | None:
    """The committed acceptance closure the model names (control_plane.triage.closure), or None.

    Amendment A9 D-51: the headline counts over this closure. A model that names no closure, or a file that is
    absent or unreadable, gives None, so the headline stays plan-wide rather than claiming a scope it cannot read.
    """
    ref = ((model.get("control_plane") or {}).get("triage") or {}).get("closure")
    if not ref:
        return None
    try:
        data = json.loads((Path(root or REPO_ROOT) / ref).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data.get("closure"), list) else None


REMAINING_KEYS = ("built_awaiting_review_or_merge", "in_progress", "ready_to_start", "waiting_on_dependencies",
                  "decision_pending", "needs_attention")
WORK_CLASSES = ("a", "a_close")


def _remaining_bucket(row: dict, item: dict) -> str:
    """Where one not-yet-done item sits. Total: every status lands in exactly one bucket."""
    st = row["status"]
    if item.get("done_by") == "decision" and st != "waiting":
        return "decision_pending"          # a decision not yet due (its inputs missing) is waiting, as the queue shows it
    if row.get("built_waiting_on_gate") or st == "review":
        return "built_awaiting_review_or_merge"
    if st == "running":
        return "in_progress"
    if st == "ready":
        return "ready_to_start"
    if st == "waiting":
        return "waiting_on_dependencies"
    return "needs_attention"               # blocked, failed, parked, conflict, unknown


def _tally(rows: list[tuple[dict, dict]]) -> dict:
    out = {"total": len(rows), "done": 0, "not_applicable": 0, "remaining": 0, **{k: 0 for k in REMAINING_KEYS}}
    for row, item in rows:
        if row["status"] == "done":
            out["done"] += 1
        elif row["status"] == "not_applicable":
            out["not_applicable"] += 1
        else:
            out["remaining"] += 1
            out[_remaining_bucket(row, item)] += 1
    return out


def reconciliation(flat: list[dict], items: dict, members: set) -> dict:
    """Account for EVERY plan item exactly once (owner request 2026-10-18); computed, never typed.

    First matching rule wins: closure member → finish path; triage retire_decision → bookkeeping decision;
    done_outside → done outside the plan path; status not_applicable or class retired → cancelled; class b → deferred;
    class a / a_close → side work; anything else → unclassified (reported, never folded into a neighbour).
    `sum_of_parts` must equal `plan_items`; test_tracker_reconciliation asserts it.
    """
    finish, side, deferred, cancelled, bookkeeping, outside, unclassified = [], [], [], [], [], [], []
    for row in flat:
        item = items[row["id"]]
        cls = (item.get("triage") or {}).get("class")
        pair = (row, item)
        if row["id"] in members:
            finish.append(pair)
        elif cls == "retire_decision":
            bookkeeping.append(pair)
        elif cls == "done_outside":
            outside.append(pair)
        elif row["status"] == "not_applicable" or cls == "retired":
            cancelled.append(pair)
        elif cls == "b":
            deferred.append(pair)
        elif cls in WORK_CLASSES:
            side.append(pair)
        else:
            unclassified.append(pair)
    parked = sum(1 for row, _ in deferred if row["status"] == "parked")
    rec = {
        "plan_items": len(flat),
        "finish_path": _tally(finish),
        "side_work": _tally(side),
        "deferred": {"total": len(deferred), "parked": parked, "other": len(deferred) - parked},
        "cancelled": {"total": len(cancelled)},
        "bookkeeping_decisions": {"total": len(bookkeeping)},
        "done_outside_plan": {"total": len(outside)},
        "unclassified": {"total": len(unclassified)},
    }
    rec["sum_of_parts"] = sum(rec[k]["total"] for k in ("finish_path", "side_work", "deferred", "cancelled",
                                                        "bookkeeping_decisions", "done_outside_plan", "unclassified"))
    return rec


def reconciliation_line(rec: dict) -> str:
    """The one-line plain-text form of `reconciliation` shown by `ky status`."""
    def part(label, t):
        left = {"built_awaiting_review_or_merge": "built and awaiting review or merge", "in_progress": "in progress",
                "ready_to_start": "ready to start", "waiting_on_dependencies": "waiting on dependencies",
                "decision_pending": "decision pending", "needs_attention": "needs attention"}
        detail = ", ".join(f"{t[k]} {left[k]}" for k in REMAINING_KEYS if t[k])
        na = f" · {t['not_applicable']} not applicable" if t["not_applicable"] else ""
        return f"{label} {t['done']}/{t['total']} done" + (f" ({t['remaining']} left: {detail})" if t["remaining"] else "") + na
    d = rec["deferred"]
    tail = f" · unclassified {rec['unclassified']['total']}" if rec["unclassified"]["total"] else ""
    return (f"All {rec['plan_items']} plan items: {part('finish path', rec['finish_path'])} · "
            f"{part('side work', rec['side_work'])} · deferred {d['total']} ({d['parked']} parked) · "
            f"cancelled {rec['cancelled']['total']} · decisions recorded {rec['bookkeeping_decisions']['total']} · "
            f"done outside plan {rec['done_outside_plan']['total']}{tail}")


def d46_headline(rows: list[dict]) -> dict:
    """A7 D-46 headline: implemented/total with activated/total beside it; close needs both."""
    return {"implemented": sum(1 for t in rows if t["status"] == "done"),
            "activated": sum(1 for t in rows if t["status"] == "done" and not t["activation_pending"]),
            "activation_pending": sum(1 for t in rows if t["activation_pending"]),
            "close_ready": bool(rows) and all(
                t["status"] == "not_applicable" or (t["status"] == "done" and not t["activation_pending"])
                for t in rows)}


def closure_headline(overall: dict, flat: list[dict], items: dict, closure: dict) -> dict:
    """Re-scope the headline to the closure's items; deferred items are a separate list (A9 D-51.3).

    The counts are per status, so a later change of what counts as done (implemented/activated) composes by
    changing the status mapping, not the scoping. A closure member the model does not contain is reported in
    `missing`, never silently dropped.
    """
    members = set(closure["closure"])
    rows = {t["id"]: t for t in flat}
    inside = [rows[i] for i in sorted(members) if i in rows]
    counts = collections.Counter(t["status"] for t in inside)
    total = len(inside)
    done = counts.get("done", 0)
    deferred = [{"id": iid, "status": rows[iid]["status"],
                 "re_entry": (items[iid].get("triage") or {}).get("re_entry")}
                for iid in sorted(rows) if iid not in members and (items[iid].get("triage") or {}).get("class") == "b"]
    return {
        **overall,
        "scope": "closure", "closure_sha256": closure.get("closure_sha256"),
        "total": total, "done": done, "not_applicable": counts.get("not_applicable", 0),
        "running": counts.get("running", 0) + counts.get("review", 0),
        "ready": counts.get("ready", 0), "waiting": counts.get("waiting", 0),
        "blocked": counts.get("blocked", 0) + counts.get("failed", 0) + counts.get("parked", 0),
        "unknown": counts.get("unknown", 0) + counts.get("conflict", 0),
        "built_waiting_on_gate": sum(1 for t in inside if t["built_waiting_on_gate"]),
        **d46_headline(inside),
        "pct": round(100 * done / total, 1) if total else 0.0,
        "by_status": dict(sorted(counts.items())),
        "missing": sorted(members - set(rows)),
        "plan_wide": {k: overall[k] for k in ("total", "done", "not_applicable", "pct")},
        "deferred": deferred,
        "reconciliation": reconciliation(flat, items, members),
    }


def build_snapshot(model: dict, events: list[dict], det_results: dict, metrics: dict,
                   health: dict, activity: dict | None = None, now: dt.datetime | None = None,
                   closure: dict | None = None, derived_done: dict | None = None) -> dict:
    """Pure function: everything the dashboard shows. det_results maps item id → detector result dict;
    activity maps stream id → git activity dict; closure (load_closure) scopes the headline (A9 D-51);
    derived_done maps code item id → merged+deployed proof (merged_deployed.derive, SR-BOLD-07)."""
    now = now or dt.datetime.now(dt.timezone.utc)
    activity = activity or {}
    ix = index_events(events)
    items = {i["id"]: dict(i) for i in model["items"]}
    guarded = model.get("control_plane", {}).get("guarded_completion") is True
    decision_outcomes = model.get("control_plane", {}).get("decision_outcomes")
    derived_done = derived_done or {}
    status = {iid: item_status(it, ix, det_results.get(iid), guarded=guarded,
                               decision_outcomes=decision_outcomes, derived=derived_done.get(iid))
              for iid, it in items.items()}

    # A final ruling is recorded independently of each consuming item's completion.
    # Seed decision items as waiting so joins/other decisions cannot consume a
    # provisional done state before its original gates have been resolved.
    recorded_decisions = {iid for iid, it in items.items()
                          if it.get("done_by") == "decision" and status[iid]["status"] == "done"}
    for iid in recorded_decisions:
        status[iid]["status"] = "waiting"

    # Start-at-merge/acceptance remains a scheduling policy only. D-39: deps_open
    # always names strict completion gates, even when work may already start.
    # deps_open_strict is a compatibility alias with exactly the same meaning.
    merged_accepted = set()
    if model.get("control_plane", {}).get("ready_at_merge") is True:
        accepted = {e.get("item") for e in events if e.get("kind") == "verdict" and e.get("result") == "ACCEPTED"
                    and e.get("phase", "pre_merge") == "pre_merge"}
        merged_accepted = {iid for iid in items if iid in accepted
                           and (det_results.get(iid) or {}).get("status") == "done"}
        # ready_at_accepted (owner direction 2026-10-08, during another campaign's merge hold): a dependency whose
        # LATEST pre-merge verdict is ACCEPTED lets dependants start, stacked on its branch, before it merges
        if model.get("control_plane", {}).get("ready_at_accepted") is True:
            latest = {}
            for e in events:
                if e.get("kind") == "verdict" and e.get("phase", "pre_merge") == "pre_merge" and e.get("item") in items:
                    latest[e["item"]] = e.get("result")
            merged_accepted |= {iid for iid, res in latest.items() if res == "ACCEPTED"}
    for s_ in status.values():
        s_["activation_pending"] = []
    # Resolve joins, recorded decisions and D-46 activation together until their strict gates stabilise.
    for _ in range(2 * len(items) + 2):
        changed = False
        for iid, it in items.items():
            s = status[iid]
            deps = it.get("depends_on", [])
            accepts_skips = it.get("accepts_not_applicable_dependencies") is True
            strict_open = open_dependencies(it, status, relaxed=is_relaxed(model, it, s))
            start_blockers = [d for d in strict_open if d not in merged_accepted]
            s["deps_open"] = strict_open
            s["deps_open_strict"] = strict_open
            if strict_open != start_blockers:
                s["deps_merged_pending_deploy"] = [d for d in strict_open if d in merged_accepted]
            if decision_outcomes and s["status"] not in ("done", "not_applicable"):
                origins = []
                for decision, needed in it.get("requires_outcome", {}).items():
                    event = decision_status(ix["decisions"].get(decision, []))[1]
                    actual = (event or {}).get("outcome")
                    if actual in decision_outcomes.get("final", []) and actual != needed:
                        origins.append(decision)
                if not accepts_skips:
                    for dep in deps:
                        if status[dep]["status"] == "not_applicable":
                            origins.extend(status[dep].get("skip_origin", [dep]))
                if origins:
                    s.update(status="not_applicable", source="decision:skip",
                             skip_origin=sorted(set(origins)), detail="required outcome or input unavailable")
                    changed = True
                    continue
            if iid in recorded_decisions and s["status"] != "not_applicable":
                new = "waiting" if strict_open else "done"
                if s["status"] != new:
                    s["status"] = new
                    changed = True
            if it.get("done_by") == "join":
                new = "done" if not strict_open else "waiting"
                if s["status"] != new:
                    s["status"] = new
                    s["evidence"] = "all dependencies done" if new == "done" else None
                    changed = True
                if new == "done" and accepts_skips:
                    s["gaps"] = sorted({origin for dep in deps for origin in
                                        status[dep].get("skip_origin", status[dep].get("gaps", []))})
            # A7 D-46: an implemented (done) item is activated only when every gate upstream, transitively, is.
            # Recomputed every pass, so it empties by itself when the last gate closes.
            pending = pending_gates(it, status) if guarded and s["status"] == "done" else []
            if s["activation_pending"] != pending:
                s["activation_pending"] = pending
                changed = True
        if not changed:
            break
    for iid, it in items.items():
        s = status[iid]
        start_blockers = [d for d in s["deps_open"] if d not in merged_accepted]
        if s.pop("soft", False) and start_blockers:
            s["status"] = "waiting"
        # An unmeasured detector on an item that cannot start yet is not an alarm: show it as waiting,
        # keep "unmeasured" in the detail, and raise it only once the item becomes startable.
        if s["status"] == "unknown" and start_blockers and not ix["items"].get(iid):
            s["status"] = "waiting"
            s["detail"] = f"unmeasured until startable — {s.get('detail', '')}"
        if s["status"] == "not_started":
            s["status"] = "ready" if not start_blockers else "waiting"

        # A5 D-39: display-only merge evidence, never a new completion state.
        # Use strict dependencies: readiness can relax a merged/accepted input
        # that is still an actual gate on completion. Non-merge detectors (e.g.
        # pr_ready or file_exists) cannot establish that code is on main.
        outcomes_met = all(
            (decision_status(ix["decisions"].get(decision, []))[1] or {}).get("outcome") == needed
            for decision, needed in it.get("requires_outcome", {}).items()
        )
        s["built_waiting_on_gate"] = bool(
            (it.get("detector") or {}).get("type") in ("branch_merged", "pr_merged")
            and (det_results.get(iid) or {}).get("status") == "done"
            and s["status"] in ("ready", "waiting", "running", "review")
            and all(step["done"] for step in s.get("steps", []))
            and outcomes_met
            and s["deps_open"]
            and all(dep in items for dep in s["deps_open"])
        )
        s["gate_blockers"] = list(s["deps_open"]) if s["built_waiting_on_gate"] else []
        # D-39 is an exclusive presentation class. Keep the underlying workflow
        # status intact for claims, strict dependency checks and guarded completion.
        s["display_status"] = "built_waiting_on_gate" if s["built_waiting_on_gate"] else s["status"]

    # a model that declares its items (relaunch plan v2.7 §6) shows each row's declaration; other models as before
    declared = isinstance(model.get("control_plane", {}).get("declarations"), dict)
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
            if declared:
                tis[-1].update({key: it.get(key) for key in DECLARATION_KEYS})
        n = len(tis)
        done = sum(1 for t in tis if t["status"] == "done")
        partial = sum((t["progress"] or 0) for t in tis if t["status"] != "done")
        tracks.append({**tr, "items": tis, "done": done, "total": n, "progress": (done + partial) / n if n else 0.0})

    flat = [t for tr in tracks for t in tr["items"]]
    counts = collections.Counter(t["display_status"] for t in flat)
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
    # a retirement decision is owner-authorised already: its refusal is STAGED for the installation action (B-2)
    # to publish, so until a final outcome is recorded it is marked and is not a question for the native
    retirements = {it["decision"] for it in model["items"] if declared and it.get("done_by") == "decision"
                   and it.get("decision") and (it.get("triage") or {}).get("class") == "retire_decision"}
    final_outcomes = (decision_outcomes or {}).get("final", ["approved", "refused"])
    for d in model["decisions"]:
        st, dev = decision_status(ix["decisions"].get(d["id"], []))
        decisions.append({**d, "status": st, "detail": (dev or {}).get("detail", ""),
                          "updated_at": (dev or {}).get("ts"), "needed_by": needed_by.get(d["id"], [])})
        if d["id"] in retirements and not (st in ("decided", "delegated") and (dev or {}).get("outcome") in final_outcomes):
            decisions[-1]["staged"] = True

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
    pending_native = sorted([d for d in decisions if d["status"] in ("requested", "pending") and d["due"]
                             and not d.get("staged")],
                            key=lambda d: (rank[d["status"]], -sum(1 for x in d["needed_by"] if status.get(x, {}).get("status") in ("ready", "waiting"))))

    overall = {"total": total, "done": counts.get("done", 0),
               **d46_headline(flat),
               "built_waiting_on_gate": sum(1 for t in flat if t["built_waiting_on_gate"]),
               "not_applicable": counts.get("not_applicable", 0),
               "running": counts.get("running", 0) + counts.get("review", 0),
               "ready": counts.get("ready", 0), "waiting": counts.get("waiting", 0),
               "blocked": counts.get("blocked", 0) + counts.get("failed", 0) + counts.get("parked", 0),
               "unknown": counts.get("unknown", 0) + counts.get("conflict", 0),
               "pct": round(100 * done_w / total, 1) if total else 0.0}
    if closure:
        overall = closure_headline(overall, flat, items, closure)

    return {
        "generated_at": now.isoformat(timespec="seconds"),
        "campaign": model.get("campaign"), "subtitle": model.get("subtitle"), "plan_ref": model.get("plan_ref"),
        "overall": overall,
        "streams": streams,
        "phases": phases,
        "tracks": tracks,
        "now": [t for t in flat if t["display_status"] in ("running", "review")],
        "next": [t for t in flat if t["display_status"] == "ready"],
        "built_waiting_on_gate": [t for t in flat if t["built_waiting_on_gate"]],
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
