#!/usr/bin/env python3
"""Projector: pure fold of PLAN.yaml + the event log + the collector's derived snapshot
-> state.json -> tracker_data.js. No wall-clock calls (Date.now-equivalents) anywhere in
the fold itself, so re-running project.py against UNCHANGED inputs (event log +
collector_snapshot.json) is byte-identical -- this is what makes 'delete state.json,
rebuild it' a safe, always-tested recovery path rather than a hopeful one.

The one place this process legitimately writes wall-clock time is when it OBSERVES a
lane's derived state changing for the first time: that observation is appended to its own
event log file (events/projector.jsonl) as a normal 'lane_state' event, evidence_class
DERIVED. On a rebuild where nothing changed, no new event is written, so the fold really
is pure over its inputs.
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import (  # noqa: E402
    COLLECTOR_SNAPSHOT_JSON, EVENTS_DIR, HEARTBEAT_JSON, PLAN_PATH, STATE_JSON, TRACKER_DATA_JS,
    atomic_write_json, atomic_write_text, ensure_runtime_dirs, load_plan,
)
from tracker_emit import emit  # noqa: E402

PROJECTOR_WRITER_ID = "projector"
STAGE_ORDER = [
    "PLANNED", "SCOUTED", "CLAIMED", "BUILDING", "VERIFYING", "ADVERSARIAL",
    "QUEUED", "ADMISSIBLE", "MERGED", "GATED", "CLOSED", "BLOCKED", "PARKED",
]


def _iso_to_epoch(iso_ts):
    import datetime
    if not iso_ts:
        return 0.0
    try:
        return datetime.datetime.strptime(iso_ts, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=datetime.timezone.utc).timestamp()
    except ValueError:
        try:
            return datetime.datetime.fromisoformat(iso_ts.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return 0.0


def load_all_events():
    events = []
    ensure_runtime_dirs()
    for path in sorted(glob.glob(os.path.join(EVENTS_DIR, "*.jsonl"))):
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        ev = json.loads(line)
                        ev["_epoch"] = _iso_to_epoch(ev.get("ts"))
                        events.append(ev)
                    except json.JSONDecodeError:
                        continue  # a torn/partial line is skipped, never crashes the fold
        except FileNotFoundError:
            continue
    events.sort(key=lambda e: (e.get("_epoch", 0), e.get("writer_id", "")))
    return events


def derive_lane_state(lane, snapshot):
    """Returns (state, evidence_class, provenance) or (None, None, None) if no derived
    evidence exists (caller falls back to claims)."""
    ea = (snapshot.get("expected_artifacts") or {}).get("value") or {}
    lane_ea = ea.get(lane["id"]) or {}
    mc = lane_ea.get("merge_commit")
    if mc and mc.get("is_ancestor_of_main"):
        closed = lane.get("_phase_status") == "CLOSED"
        return ("CLOSED" if closed else "MERGED", "DERIVED",
                f"git merge-base --is-ancestor {mc['sha']} origin/main")

    branches = (snapshot.get("git_lane_branches") or {}).get("value") or {}
    prs = (snapshot.get("github_prs") or {}).get("value") or {}
    candidate_branch = None
    for name in branches:
        short = name.split("/")[-1].lower()
        if short == lane["id"].lower() or short.startswith(lane["id"].lower() + "-"):
            candidate_branch = name
            break
    if candidate_branch:
        info = branches[candidate_branch]
        ab = info.get("ahead_behind_main")
        pr = prs.get(candidate_branch)
        if pr:
            if pr.get("is_draft"):
                return ("BUILDING", "DERIVED", f"gh pr list: {pr['url']} is a draft")
            if pr.get("check_rollup") == "FAILURE":
                return ("BUILDING", "DERIVED", f"gh pr list: {pr['url']} checks red")
            if pr.get("check_rollup") == "SUCCESS" and pr.get("merge_state_status") == "CLEAN":
                return ("QUEUED", "DERIVED", f"gh pr list: {pr['url']} checks green, mergeable")
            return ("VERIFYING", "DERIVED", f"gh pr list: {pr['url']} checks pending")
        if ab and ab.get("ahead", 0) == 0 and ab.get("behind", 0) >= 0:
            return ("MERGED", "DERIVED",
                    f"branch {candidate_branch} 0 commits ahead of origin/main (no open PR)")
        return ("BUILDING", "DERIVED", f"branch {candidate_branch} exists, {ab} vs origin/main")

    for p in lane_ea.get("paths", []):
        if p.get("exists"):
            return ("BUILDING", "DERIVED", f"expected artifact present: {p['path']}")

    return (None, None, None)


def latest_claim(events, lane_id, kind="lane_state"):
    """A CLAIM is a real external agent's self-report -- explicitly NOT the projector's own
    bookkeeping events (writer_id == PROJECTOR_WRITER_ID), which record the projector's own
    conclusion (itself possibly a fallback with no strong evidence) and must never be read
    back as if an agent had claimed something."""
    for ev in reversed(events):
        if (ev.get("kind") == kind and ev.get("lane") == lane_id
                and ev.get("evidence_class") == "CLAIMED"
                and ev.get("writer_id") != PROJECTOR_WRITER_ID):
            return ev
    return None


def last_projector_state(events, lane_id):
    """The projector's own last recorded conclusion for this lane, identified by
    writer_id, regardless of what evidence_class that conclusion carried -- used only to
    compute age-in-state, never fed back into latest_claim()."""
    for ev in reversed(events):
        if (ev.get("writer_id") == PROJECTOR_WRITER_ID and ev.get("kind") == "lane_state"
                and ev.get("lane") == lane_id):
            return ev
    return None


def anomaly_already_recorded(events, lane_id, claim_epoch):
    for ev in events:
        if (ev.get("kind") == "anomaly" and ev.get("lane") == lane_id
                and ev.get("payload", {}).get("claim_ts_epoch") == claim_epoch):
            return True
    return False


CONTRADICTS = {"MERGED", "CLOSED"}


def fold(plan, snapshot, events, as_of_epoch):
    lanes_by_id = {}
    phase_status = {p["id"]: p["status"] for p in plan["phases"]}
    for lane in plan["lanes"]:
        lane = dict(lane)
        lane["_phase_status"] = phase_status.get(lane["phase"], "PLANNED")
        lanes_by_id[lane["id"]] = lane

    new_events_to_write = []
    out_lanes = []
    for lane_id, lane in lanes_by_id.items():
        derived_state, derived_ec, derived_prov = derive_lane_state(lane, snapshot)
        claim = latest_claim(events, lane_id)

        if derived_state:
            state, evidence_class, provenance = derived_state, derived_ec, derived_prov
        elif claim:
            state, evidence_class, provenance = claim["payload"].get("state", "CLAIMED"), "CLAIMED", claim.get("provenance")
        else:
            state, evidence_class, provenance = "PLANNED", "DERIVED", "PLAN.yaml default (no evidence yet)"

        if claim and derived_state and claim["payload"].get("state") in CONTRADICTS:
            claimed_state = claim["payload"].get("state")
            evidence_says_not_merged = derived_state not in ("MERGED", "CLOSED")
            if claimed_state in CONTRADICTS and evidence_says_not_merged:
                if not anomaly_already_recorded(events, lane_id, claim["_epoch"]):
                    new_events_to_write.append(dict(
                        writer_id=PROJECTOR_WRITER_ID, kind="anomaly", lane=lane_id,
                        evidence_class="DERIVED",
                        provenance="projector.py contradiction check",
                        payload={
                            "message": f"{lane_id}: claimed '{claimed_state}' by {claim.get('writer_id')} "
                                       f"but derived evidence says '{derived_state}' ({derived_prov})",
                            "claim_ts_epoch": claim["_epoch"], "claimed_state": claimed_state,
                            "derived_state": derived_state,
                        },
                    ))

        last_transition = last_projector_state(events, lane_id)
        if not last_transition or last_transition["payload"].get("state") != state or last_transition.get("evidence_class") != evidence_class:
            new_events_to_write.append(dict(
                writer_id=PROJECTOR_WRITER_ID, kind="lane_state", lane=lane_id,
                # This is the projector's own bookkeeping record of ITS OWN conclusion
                # (which may itself be the honest "PLANNED, no evidence yet" default) --
                # reuse the same evidence_class already computed for display above. Never
                # invert to CLAIMED just because there was no strong signal: that would
                # make this bookkeeping event indistinguishable from a real agent claim on
                # the next fold (see latest_claim()'s writer_id exclusion, which exists
                # specifically to prevent that feedback loop).
                evidence_class=evidence_class,
                provenance=provenance or "no evidence",
                payload={"state": state},
            ))
            transition_epoch = as_of_epoch
        else:
            transition_epoch = last_transition["_epoch"]

        out_lanes.append({
            "id": lane_id, "title": lane["title"], "phase": lane["phase"],
            "depends_on": lane["depends_on"], "state": state,
            "evidence_class": evidence_class, "provenance": provenance,
            "age_in_state_seconds": max(0, as_of_epoch - transition_epoch),
            "branch": next((b for b in (snapshot.get("git_lane_branches") or {}).get("value", {})
                             if b.split("/")[-1].lower().startswith(lane_id.lower())), None),
        })

    out_lanes.sort(key=lambda entry: -entry["age_in_state_seconds"])
    return out_lanes, new_events_to_write


def critical_path(plan, out_lanes):
    by_id = {lane["id"]: lane for lane in out_lanes}
    depends = {lane["id"]: lane["depends_on"] for lane in plan["lanes"]}
    memo = {}

    def longest(lid, seen):
        if lid in memo:
            return memo[lid]
        if lid in seen:
            return []
        seen = seen | {lid}
        best = []
        for dep in depends.get(lid, []):
            cand = longest(dep, seen)
            if len(cand) > len(best):
                best = cand
        result = best + [lid]
        memo[lid] = result
        return result

    all_paths = [longest(lid, frozenset()) for lid in depends]
    path = max(all_paths, key=len) if all_paths else []
    blocking = next((lid for lid in path if by_id.get(lid, {}).get("state") not in ("MERGED", "CLOSED")), None)
    return path, blocking


def fold_budget(plan, events):
    ceilings = plan.get("budgets_usd", {})
    spent = {ph["id"]: 0.0 for ph in plan["phases"]}
    for ev in events:
        if ev.get("kind") == "budget":
            phase = ev.get("payload", {}).get("phase")
            amount = ev.get("payload", {}).get("spent_usd")
            if phase in spent and isinstance(amount, (int, float)):
                spent[phase] += amount
    return {ph: {"ceiling_usd": ceilings.get(ph), "spent_usd": round(spent.get(ph, 0.0), 2)} for ph in ceilings}


def fold_daemon_health(events):
    last_hb = None
    resurrections = 0
    signal_failures = []
    for ev in events:
        if ev.get("kind") == "daemon":
            payload = ev.get("payload", {})
            if payload.get("event") == "resurrection":
                resurrections += 1
            if payload.get("event") == "signal_failure":
                signal_failures.append(payload)
            if payload.get("event") == "cycle":
                last_hb = ev
    return {"resurrection_count": resurrections, "recent_signal_failures": signal_failures[-10:],
            "last_daemon_cycle_event": last_hb}


def project(write_new_events=True):
    plan = load_plan()
    ensure_runtime_dirs()
    try:
        with open(COLLECTOR_SNAPSHOT_JSON, encoding="utf-8") as f:
            snapshot = json.load(f)
    except FileNotFoundError:
        snapshot = {"collected_at": None}

    events = load_all_events()
    # as_of_epoch ("observer freshness") is a pure function of collector_snapshot.json's
    # own collected_at -- NEVER of event timestamps. Event writes (including this same
    # function's own transition/anomaly events, below) happen at real wall-clock time and
    # must not feed back into as_of_epoch, or two back-to-back runs with an unchanged
    # collector snapshot would compute different values and state.json would not rebuild
    # byte-identically after a delete.
    if snapshot.get("collected_at"):
        as_of_epoch = _iso_to_epoch(snapshot["collected_at"])
    else:
        event_epochs = [ev["_epoch"] for ev in events] or [0.0]
        as_of_epoch = max(event_epochs)

    out_lanes, new_events = fold(plan, snapshot, events, as_of_epoch)

    if write_new_events and new_events:
        for ne in new_events:
            emit(ne["writer_id"], ne["kind"], ne["payload"], lane=ne.get("lane"),
                 evidence_class=ne["evidence_class"], provenance=ne["provenance"])
        events = load_all_events()
        out_lanes, _ = fold(plan, snapshot, events, as_of_epoch)

    anomalies = [ev for ev in events if ev.get("kind") == "anomaly"]
    path, blocking_lane = critical_path(plan, out_lanes)

    lane_states = {lane["id"]: lane["state"] for lane in out_lanes}
    last_progress_epoch = max(
        [lane["age_in_state_seconds"] * -1 + as_of_epoch for lane in out_lanes] + [0.0]
    )
    building_lanes = [lane for lane in out_lanes if lane["state"] in ("BUILDING", "VERIFYING", "ADVERSARIAL", "QUEUED")]
    stalled = bool(building_lanes) and (as_of_epoch - last_progress_epoch) > (20 * 60) if building_lanes else False

    import datetime
    generated_at = datetime.datetime.fromtimestamp(as_of_epoch, tz=datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    current_phase = next((p for p in plan["phases"] if p["status"] != "CLOSED"), plan["phases"][-1])

    heartbeat = {}
    if os.path.exists(HEARTBEAT_JSON):
        try:
            with open(HEARTBEAT_JSON, encoding="utf-8") as f:
                heartbeat = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            heartbeat = {}

    state = {
        "schema_version": "2.0",
        "generated_at": generated_at,
        "plan_version": plan["plan_version"],
        "current_phase": current_phase["id"],
        "phases": plan["phases"],
        "lanes": out_lanes,
        "critical_path": {"path": path, "blocking_lane": blocking_lane},
        "anomalies": [
            {"ts": a["ts"], "lane": a.get("lane"), "message": a["payload"].get("message")}
            for a in anomalies
        ],
        "budget": fold_budget(plan, events),
        "shared_surfaces": {k: v for k, v in (snapshot.get("shared_surfaces") or {}).items()},
        "github_rate_limit": snapshot.get("github_rate_limit"),
        "daemon_health": fold_daemon_health(events),
        "selftest_last": heartbeat.get("selftest_last"),
        "daemon_pid": heartbeat.get("pid"),
        "stalled": stalled,
        "last_progress_at": datetime.datetime.fromtimestamp(last_progress_epoch, tz=datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event_feed_recent": [
            {"ts": e["ts"], "writer_id": e["writer_id"], "lane": e.get("lane"), "kind": e["kind"],
             "evidence_class": e["evidence_class"], "payload": e["payload"]}
            for e in events[-50:]
        ],
    }
    atomic_write_json(STATE_JSON, state)
    atomic_write_text(TRACKER_DATA_JS, "window.TRACKER_DATA = " + json.dumps(state, indent=2, sort_keys=True) + ";\n")
    return state


if __name__ == "__main__":
    s = project()
    print(f"projected: phase={s['current_phase']} lanes={len(s['lanes'])} anomalies={len(s['anomalies'])}")
