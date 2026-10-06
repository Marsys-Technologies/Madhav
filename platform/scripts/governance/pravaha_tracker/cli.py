"""pravaha — the one command every participant uses to read and move the campaign.

The tracker is the work queue: a stream asks it what is ready (`next`), claims an item (`start`),
reports steps as it goes (`step`), and closes with evidence (`done`). Because the streams take their
work FROM the tracker, the tracker cannot fall behind the work.

  pravaha preflight --stream A                 session-start checks + heartbeat; exit≠0 → do not start work
  pravaha next      --stream A                 what A may start now (and what is running/blocked)
  pravaha status   [--stream A]                one-screen summary
  pravaha start     A2.1 --stream A [--detail ..]
  pravaha step      A2.1 aspect_direction --stream A [--evidence ..]
  pravaha progress  A2.1 0.4 --stream A [--detail ..]
  pravaha review    A2.1 --stream A --detail "K3 review requested"
  pravaha done      A2.1 --stream A --evidence "PR #2760"
  pravaha block     A2.1 --stream A --detail "waiting for N-12"
  pravaha heartbeat --stream A --detail "running battery"
  pravaha metric    NAME VALUE --stream A [--detail ..]
  pravaha note      --stream A --detail ".."
  pravaha request   D-RQ1 --stream B --detail "packet at <path>"      (asks the native)
  pravaha decide    D-RQ1 --detail "what was decided" [--as steward]   (the native's ruling)

Message bus (no human relays messages):
  pravaha send      --to A|B|C --detail ".." [--file path] [--ref ITEM]   steward -> stream
  pravaha report    --stream A --detail ".." [--ref ITEM]             stream -> steward
  pravaha inbox     --stream A | --steward [--wait SECONDS] [--json]  unacked messages; --wait blocks
  pravaha ack       MSG_ID --stream A | --steward [--detail ..]       mark a message acted on

Stream from --stream or $PRAVAHA_STREAM. Exit codes: 0 ok · 2 refused (nothing written) ·
3 cannot write the event log (STOP work and tell the native) · 4 preflight failed.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    __package__ = "pravaha_tracker"

from pravaha_tracker.events import EventError, append  # noqa: E402
from pravaha_tracker.claims import ClaimError, claim_item, renew_claim, release_claim  # noqa: E402
from pravaha_tracker.detectors import git_activity  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
HOME = os.environ.get("PRAVAHA_HOME", "/Users/Dev/pravaha")
EVENTS = os.environ.get("PRAVAHA_EVENTS", os.path.join(HOME, "run", "EVENTS.jsonl"))
SNAPSHOT = os.path.join(HOME, "run", "snapshot.json")
MODEL = os.environ.get("PRAVAHA_PLAN_MODEL", os.path.join(REPO_ROOT, "00_ARCHITECTURE", "control", "pravaha", "plan_model.json"))
URL = os.environ.get("PRAVAHA_URL", "http://127.0.0.1:" + os.environ.get("PRAVAHA_TRACKER_PORT", "8766"))


def hold_path() -> str:
    return os.environ.get("PRAVAHA_HOLD") or os.path.join(os.environ.get("PRAVAHA_HOME", HOME), "run", "PRAVAHA_HOLD")


def load_model() -> dict:
    with open(MODEL, encoding="utf-8") as f:
        return json.load(f)


def get(path: str, timeout: float = 3.0):
    """Ask the live tracker; fall back to the last persisted snapshot (and say so)."""
    try:
        with urllib.request.urlopen(URL + path, timeout=timeout) as r:  # noqa: S310
            return json.loads(r.read().decode()), "live"
    except Exception:  # noqa: BLE001
        try:
            with open(SNAPSHOT, encoding="utf-8") as f:
                return {"_snapshot": json.load(f)}, "stale-snapshot"
        except (OSError, ValueError):
            return None, "unavailable"


def actor_for(a) -> str:
    if getattr(a, "as_", None):
        return a.as_
    s = (a.stream or os.environ.get("PRAVAHA_STREAM", "")).strip().upper()
    if not s:
        raise SystemExit("error: give --stream A|B (or set PRAVAHA_STREAM)")
    return f"stream-{s}"


def cmd_claim_lifecycle(a) -> int:
    """Claims always read the locked event log; the dashboard snapshot is never authority."""
    try:
        model = load_model()
        worker = a.worker or os.environ.get("KY_LANE", "")
        if not worker:
            raise ClaimError("worker id is required")
        if a.cmd == "claim":
            stream = (a.stream or os.environ.get("PRAVAHA_STREAM") or os.environ.get("KY_STREAM") or "").upper()
            event = claim_item(EVENTS, model, a.item, stream, worker, a.lease,
                               branch=a.branch, head=a.head, step=a.step)
        else:
            record = os.path.join(os.path.dirname(EVENTS), "claims", worker + ".json")
            with open(record, encoding="utf-8") as handle:
                current = json.load(handle)
            if a.cmd == "renew":
                event = renew_claim(EVENTS, model, current["item"], worker, current["claim_id"],
                                    a.lease, branch=a.branch, head=a.head, step=a.step)
            else:
                event = release_claim(EVENTS, current["item"], worker, current["claim_id"])
        print(json.dumps(event, ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError, ClaimError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2


def write(ev: dict) -> int:
    try:
        model = load_model()
    except (OSError, ValueError) as exc:
        print(f"refused: cannot read the plan model ({exc})", file=sys.stderr)
        return 2
    try:
        out = append(EVENTS, {k: v for k, v in ev.items() if v not in (None, "")}, model)
    except EventError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"CANNOT WRITE THE EVENT LOG ({exc}). Stop work and tell the native — "
              "work that cannot be seen on the tracker must not continue.", file=sys.stderr)
        return 3
    print(json.dumps(out, ensure_ascii=False))
    return 0


def _items_from(res) -> list[dict]:
    snap = res.get("_snapshot") if isinstance(res, dict) and "_snapshot" in res else None
    if snap:
        return [t for tr in snap.get("tracks", []) for t in tr["items"]]
    return []


def cmd_next(a) -> int:
    s = (a.stream or os.environ.get("PRAVAHA_STREAM", "")).upper()
    res, via = get(f"/api/next?stream={s}")
    if res is None:
        print("tracker unreachable and no snapshot on disk", file=sys.stderr)
        return 3
    if via != "live":
        flat = [t for t in _items_from(res) if not s or t.get("owner") == s]
        res = {"running": [t for t in flat if t["status"] in ("running", "review")],
               "ready": [t for t in flat if t["status"] == "ready"],
               "blocked": [t for t in flat if t["status"] in ("blocked", "failed", "parked", "conflict")]}
        print(f"WARNING: tracker not reachable — showing the last saved snapshot. Start it: launchctl kickstart -k gui/$(id -u)/com.madhav.pravaha.tracker", file=sys.stderr)
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
        return 0
    for label in ("running", "ready", "blocked"):
        rows = res.get(label, [])
        print(f"{label.upper()} ({len(rows)})")
        for t in rows:
            extra = f" — {t.get('detail')}" if t.get("detail") else ""
            print(f"  {t['id']:<8} {t['title']}{extra}")
    return 0


def cmd_status(a) -> int:
    res, via = get("/api/state")
    snap = res.get("_snapshot") if (res and "_snapshot" in res) else res
    if not snap:
        print("tracker unreachable and no snapshot on disk", file=sys.stderr)
        return 3
    o = snap["overall"]
    print(f"{snap.get('campaign')} — {o['pct']}% · done {o['done']}/{o['total']} · running {o['running']} · ready {o['ready']} · "
          f"blocked {o['blocked']} · unmeasured {o['unknown']}   [{via}, v{snap.get('version')}]")
    for st in snap.get("streams", []):
        if a.stream and st["id"] != a.stream.upper():
            continue
        hb = st.get("heartbeat") or {}
        g = st.get("git") or {}
        print(f"  Stream {st['id']} ({st.get('name')}) · {st['liveness']} · {st['done']}/{st['total']} done · "
              f"heartbeat {int(hb['age_s'])}s ago" if hb.get("age_s") is not None else f"  Stream {st['id']} ({st.get('name')}) · {st['liveness']} · no heartbeat yet")
        for t in st.get("running", []):
            print(f"     running  {t['id']} {t['title']}")
        if g.get("subject"):
            print(f"     last commit {g.get('last_commit')} on {g.get('branch')}: {g.get('subject')}")
    nq = snap.get("native_queue", [])
    if nq and not a.stream:
        print(f"  Native decisions open: {', '.join(d['id'] for d in nq)}")
    return 0


def cmd_preflight(a) -> int:
    s = (a.stream or os.environ.get("PRAVAHA_STREAM", "")).upper()
    problems = []
    try:
        model = load_model()
    except (OSError, ValueError) as exc:
        print(f"FAIL plan model unreadable: {exc}")
        return 4
    stream = next((x for x in model.get("streams", []) if x["id"] == s), None)
    if not stream:
        print(f"FAIL unknown stream {s!r}")
        return 4
    h, via = get("/api/health")
    if via != "live" or not h or not h.get("ok", False):
        problems.append("tracker is not live on " + URL)
    cwd = os.path.realpath(os.getcwd())
    wts = [os.path.realpath(w) for w in stream.get("worktrees", [])]
    wt = next((w for w in wts if cwd == w or cwd.startswith(w + os.sep)), None)
    if wts and wt is None:
        problems.append(f"you are in {cwd}, but Stream {s} works in one of: {', '.join(wts)}")
    act = git_activity(wt) if wt else {}
    want = stream.get("branch_pattern")
    # Between claims a lane intentionally sits at detached origin/main.
    worker = os.environ.get("KY_LANE", "")
    claim_file = os.path.join(HOME, "run", "claims", worker + ".json") if worker else ""
    active_claim = False
    if claim_file and os.path.exists(claim_file):
        try:
            with open(claim_file, encoding="utf-8") as handle:
                active_claim = json.load(handle).get("state") in ("acquired", "renewed")
        except (OSError, ValueError):
            problems.append("claim record is unreadable")
    detached_without_claim = act.get("branch") == "HEAD" and not active_claim
    if want and act.get("branch") and not detached_without_claim and not __import__("re").match(want, act["branch"]):
        problems.append(f"worktree is on branch {act.get('branch')}, expected {want}")
    if os.path.exists(hold_path()):
        problems.append("HOLD switch is on — the native has paused new work")
    rc = write({"kind": "heartbeat", "actor": f"stream-{s}", "detail": "preflight: " + ("ok" if not problems else "FAILED: " + "; ".join(problems))})
    if rc != 0:
        problems.append("cannot write the event log")
    for p in problems:
        print("FAIL " + p)
    if problems:
        return 4
    print(f"OK Stream {s} ({stream.get('name')}) — tracker live, worktree {wt}, branch {act.get('branch')}. Now run: pravaha next --stream {s}")
    return 0


def _read_events() -> list[dict]:
    out = []
    try:
        with open(EVENTS, encoding="utf-8") as f:
            for raw in f:
                try:
                    out.append(json.loads(raw))
                except ValueError:
                    continue
    except OSError:
        pass
    return out


def _party(a) -> str:
    if getattr(a, "steward", False):
        return "steward"
    s = (a.stream or os.environ.get("PRAVAHA_STREAM", "")).strip().upper()
    if not s:
        raise SystemExit("error: give --stream A|B or --steward")
    return s


def _unacked(party: str) -> list[dict]:
    evs = _read_events()
    acked = set()
    for e in evs:
        if e.get("kind") == "ack":
            who = "steward" if e.get("actor") in ("steward", "native") else (e.get("actor", "").split("-", 1)[-1][:1].upper())
            acked.add((who, e.get("msg_id")))
    return [e for e in evs if e.get("kind") == "message" and e.get("to") == party and (party, e.get("msg_id")) not in acked]


def cmd_inbox(a) -> int:
    import time
    party = _party(a)
    deadline = time.time() + max(0, int(a.wait or 0))
    while True:
        msgs = _unacked(party)
        if msgs or time.time() >= deadline:
            break
        time.sleep(3)
    if a.json:
        print(json.dumps(msgs, ensure_ascii=False, indent=1))
    else:
        print(f"INBOX {party}: {len(msgs)} unacked")
        for m in msgs:
            ref = f" [{m['ref']}]" if m.get("ref") else ""
            print(f"--- {m['msg_id']} from {m.get('actor')} at {m.get('ts')}{ref}\n{m.get('detail')}")
    return 0 if msgs else 1


def _msg_id() -> str:
    import datetime as _dt
    import secrets
    return _dt.datetime.now(_dt.timezone.utc).strftime("M%Y%m%dT%H%M%S") + "-" + secrets.token_hex(2)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="pravaha", description="Pravāha campaign CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name, *pos, evidence=False, detail=True):
        p = sub.add_parser(name)
        for x in pos:
            p.add_argument(x)
        p.add_argument("--stream")
        p.add_argument("--as", dest="as_", choices=["steward", "native"])
        if detail:
            p.add_argument("--detail", default="")
        if evidence:
            p.add_argument("--evidence")
        return p

    p = sub.add_parser("next"); p.add_argument("--stream"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("status"); p.add_argument("--stream")
    p = sub.add_parser("preflight"); p.add_argument("--stream")
    p = sub.add_parser("claim"); p.add_argument("item"); p.add_argument("--stream"); p.add_argument("--worker")
    p.add_argument("--lease", type=int, default=5400); p.add_argument("--branch"); p.add_argument("--head"); p.add_argument("--step")
    p = sub.add_parser("renew"); p.add_argument("--worker"); p.add_argument("--lease", type=int, default=5400)
    p.add_argument("--branch"); p.add_argument("--head"); p.add_argument("--step")
    p = sub.add_parser("release"); p.add_argument("--worker")
    p = sub.add_parser("verdict"); p.add_argument("item"); p.add_argument("--stream")
    p.add_argument("--head"); p.add_argument("--artifact-digest")
    p.add_argument("--phase", choices=["pre_merge", "post_deploy", "artifact"], default="pre_merge")
    p.add_argument("--result", choices=["ACCEPTED", "REJECTED"], required=True)
    p.add_argument("--detail", required=True)
    add("start", "item"); add("review", "item"); add("block", "item"); add("park", "item"); add("fail", "item")
    add("done", "item", evidence=True)
    add("step", "item", "step_name", evidence=True)
    add("progress", "item", "value")
    add("heartbeat"); add("note")
    add("metric", "name", "value")
    add("request", "decision")
    p = sub.add_parser("send"); p.add_argument("--to", required=True); p.add_argument("--detail", default="")
    p.add_argument("--file"); p.add_argument("--ref"); p.add_argument("--as", dest="as_", default="steward")
    p = sub.add_parser("report"); p.add_argument("--stream"); p.add_argument("--detail", required=True); p.add_argument("--ref")
    p = sub.add_parser("inbox"); p.add_argument("--stream"); p.add_argument("--steward", action="store_true")
    p.add_argument("--wait", type=int, default=0); p.add_argument("--json", action="store_true")
    p = sub.add_parser("ack"); p.add_argument("msg_id"); p.add_argument("--stream"); p.add_argument("--steward", action="store_true")
    p.add_argument("--detail", default="")
    p = sub.add_parser("decide"); p.add_argument("decision"); p.add_argument("--detail", required=True)
    p.add_argument("--outcome", choices=["approved", "refused", "deferred", "insufficient_evidence"])
    p.add_argument("--as", dest="as_", choices=["native", "steward"], default="native")
    p.add_argument("--delegated", action="store_true")
    a = ap.parse_args(argv)

    if a.cmd == "next":
        return cmd_next(a)
    if a.cmd == "status":
        return cmd_status(a)
    if a.cmd == "preflight":
        return cmd_preflight(a)
    if a.cmd in ("claim", "renew", "release"):
        return cmd_claim_lifecycle(a)
    if a.cmd == "inbox":
        return cmd_inbox(a)
    if a.cmd == "send":
        body = a.detail
        if a.file:
            with open(a.file, encoding="utf-8") as f:
                body = (body + "\n\n" if body else "") + f.read()
        actor = a.as_ if a.as_ in ("steward", "native") else f"stream-{a.as_.upper()}"
        return write({"kind": "message", "actor": actor, "to": a.to.upper() if a.to.lower() != "steward" else "steward",
                      "msg_id": _msg_id(), "ref": a.ref, "detail": body.strip()})
    if a.cmd == "report":
        return write({"kind": "message", "actor": actor_for(a), "to": "steward", "msg_id": _msg_id(), "ref": a.ref, "detail": a.detail})
    if a.cmd == "ack":
        actor = "steward" if a.steward else actor_for(a)
        return write({"kind": "ack", "actor": actor, "msg_id": a.msg_id, "detail": a.detail})
    if a.cmd == "decide":
        return write({"kind": "decision", "actor": a.as_, "decision": a.decision,
                      "state": "delegated" if a.delegated else "decided", "outcome": a.outcome,
                      "detail": a.detail})
    actor = actor_for(a)
    if a.cmd == "verdict":
        return write({"kind": "verdict", "actor": actor, "item": a.item, "head": a.head,
                      "artifact_digest": a.artifact_digest, "phase": a.phase,
                      "result": a.result, "detail": a.detail})
    state_of = {"start": "running", "review": "review", "block": "blocked", "park": "parked", "fail": "failed", "done": "done"}
    if a.cmd in state_of:
        return write({"kind": "item", "actor": actor, "item": a.item, "state": state_of[a.cmd],
                      "detail": a.detail, "evidence": getattr(a, "evidence", None)})
    if a.cmd == "step":
        return write({"kind": "item", "actor": actor, "item": a.item, "state": "done", "step": a.step_name,
                      "detail": a.detail, "evidence": a.evidence or f"step {a.step_name} reported by {actor}"})
    if a.cmd == "progress":
        return write({"kind": "item", "actor": actor, "item": a.item, "state": "running",
                      "progress": max(0.0, min(1.0, float(a.value))), "detail": a.detail})
    if a.cmd == "heartbeat":
        return write({"kind": "heartbeat", "actor": actor, "detail": a.detail})
    if a.cmd == "note":
        return write({"kind": "note", "actor": actor, "detail": a.detail})
    if a.cmd == "metric":
        return write({"kind": "metric", "actor": actor, "name": a.name, "value": a.value, "detail": a.detail})
    if a.cmd == "request":
        return write({"kind": "decision", "actor": actor, "decision": a.decision, "state": "requested", "detail": a.detail})
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
