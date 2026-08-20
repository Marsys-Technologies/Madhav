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
    BLIND_WINDOW_JSON, COLLECTOR_SNAPSHOT_JSON, EVENTS_DIR, HEARTBEAT_JSON, PLAN_PATH, STATE_JSON,
    TRACKER_DATA_JS, atomic_write_json, atomic_write_text, classify_code_provenance,
    ensure_runtime_dirs, load_plan,
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


def lane_identifiers(lane):
    """Every identifier this lane answers to: its own id plus its gate id (the swarm names
    branches and PRs by GATE -- `pariprashna/g1-a-safety-gate`, "(G3-E/G3-G)" -- while this
    plan's lane ids are P<phase>-<letter>. Matching only on the lane id is why 46 of 53
    lanes read PLANNED for 17.5h while two whole phases shipped)."""
    ids = [lane["id"].upper()]
    if lane.get("gate"):
        ids.append(lane["gate"].upper())
    return ids


def find_lane_branch(lane, snapshot):
    """Single source of truth for lane->branch matching, used BOTH for state derivation and
    for the table's Branch column. These used to be two different rules -- the display
    column matched on a bare prefix and so showed e.g. P1-C -> `p1-close-tracker` and
    P2-F -> `p2-final`, branches those lanes have nothing to do with, while the state logic
    (correctly) matched neither. Two rules for one question is how a page shows a lane
    attached to a branch it isn't deriving anything from."""
    branches = (snapshot.get("git_lane_branches") or {}).get("value") or {}
    for name in sorted(branches):
        short = name.split("/")[-1].lower()
        for ident in lane_identifiers(lane):
            i = ident.lower()
            if short == i or short.startswith(i + "-"):
                return name
    return None


_CONDUCTOR_STAGE_TO_STATE = {
    "queued": "PLANNED", "building": "BUILDING", "verifying": "VERIFYING",
    "refuting": "ADVERSARIAL", "admissible": "ADMISSIBLE", "merged": "MERGED",
    "parked": "PARKED", "blocked": "BLOCKED", "closed": "CLOSED",
}


def conductor_claim_for_lane(lane, snapshot):
    """The conductor's own SWARM_TRACKER.json entry for this lane, if any. Returns
    (state, provenance) or (None, None). Always rendered CLAIMED by the caller: this is the
    subject describing itself, and derived evidence always wins over it."""
    cs = snapshot.get("conductor_state") or {}
    if cs.get("evidence_class") != "DERIVED":
        return (None, None)
    stages = (cs.get("value") or {}).get("lane_stages") or {}
    for ident in lane_identifiers(lane):
        stage = stages.get(ident)
        if stage:
            mapped = _CONDUCTOR_STAGE_TO_STATE.get(str(stage).lower())
            if mapped:
                return (mapped, f"conductor SWARM_TRACKER.json: {ident} role_stage="
                                f"{stage!r} (self-report, not derived)")
    return (None, None)


def derive_lane_state(lane, snapshot):
    """Returns (state, evidence_class, provenance) or (None, None, None) if NO derived
    evidence exists at all (caller then falls back to the conductor's claim, and failing
    that to UNOBSERVABLE -- never to a fabricated PLANNED)."""
    # (1) PRIMARY, and the fix for this tracker's central defect: a merged PR that declares
    # it implements this lane. A merge is a fact. This is the only source that actually
    # tracks the swarm's real progress -- see collect.extract_lane_identifiers.
    merged = (snapshot.get("recent_merged_prs") or {}).get("value") or []
    idents = set(lane_identifiers(lane))
    for pr in merged:
        implements = {i.upper() for i in (pr.get("implements") or [])}
        if not (idents & implements):
            continue
        if not pr.get("is_ancestor_of_mirror_main"):
            # gh says merged but the mirror hasn't got it yet -- do not claim MERGED off a
            # commit this tracker cannot actually see. The ref-lag anomaly covers it.
            continue
        matched = sorted(idents & implements)
        return ("MERGED", "DERIVED",
                f"PR #{pr['number']} implements {', '.join(matched)}; merge commit "
                f"{pr['merge_commit_sha'][:10]} is an ancestor of main (mirror)")

    ea = (snapshot.get("expected_artifacts") or {}).get("value") or {}
    lane_ea = ea.get(lane["id"]) or {}
    mc = lane_ea.get("merge_commit")
    if mc and mc.get("is_ancestor_of_main"):
        return ("MERGED", "DERIVED",
                f"git merge-base --is-ancestor {mc['sha']} main (mirror)")

    prs = (snapshot.get("github_prs") or {}).get("value") or {}
    candidate_branch = find_lane_branch(lane, snapshot)
    branches = (snapshot.get("git_lane_branches") or {}).get("value") or {}
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
                    f"branch {candidate_branch} 0 commits ahead of main (mirror; no open PR)")
        return ("BUILDING", "DERIVED", f"branch {candidate_branch} exists, {ab} vs main (mirror)")

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


def gh_mirror_anomaly_already_recorded(events, key):
    for ev in events:
        if ev.get("kind") == "anomaly" and ev.get("payload", {}).get("gh_mirror_divergence_key") == key:
            return True
    return False


def gh_mirror_anomalies(snapshot, events):
    """Item 4: a free consistency check now that two independent sources exist. gh is
    network-live; the mirror could lag behind it. If gh reports a PR merged whose merge
    commit is NOT an ancestor of the mirror's main, that is a genuine, real divergence --
    exactly the false condition PR #1341 needed caught (a confidently-wrong lease/merge
    cell)."""
    rmp = snapshot.get("recent_merged_prs") or {}
    if rmp.get("evidence_class") != "DERIVED":
        return []
    new_events = []
    for pr in rmp.get("value") or []:
        if pr.get("is_ancestor_of_mirror_main") is False:
            key = f"{pr['number']}:{pr['merge_commit_sha']}"
            if not gh_mirror_anomaly_already_recorded(events, key):
                new_events.append(dict(
                    writer_id=PROJECTOR_WRITER_ID, kind="anomaly", lane=None,
                    evidence_class="DERIVED",
                    provenance="projector.py gh-vs-mirror consistency check",
                    payload={
                        "message": f"PR #{pr['number']} ({pr.get('head_ref')}) reported MERGED by gh "
                                   f"(merge commit {pr['merge_commit_sha'][:10]}) but that commit is NOT "
                                   f"an ancestor of the mirror's main -- refs are lagging, or something is wrong.",
                        "gh_mirror_divergence_key": key,
                        "pr_number": pr["number"], "merge_commit_sha": pr["merge_commit_sha"],
                    },
                ))
    return new_events


def fold(plan, snapshot, events, as_of_epoch):
    lanes_by_id = {}
    for lane in plan["lanes"]:
        lane = dict(lane)
        lanes_by_id[lane["id"]] = lane

    new_events_to_write = []
    out_lanes = []
    for lane_id, lane in lanes_by_id.items():
        derived_state, derived_ec, derived_prov = derive_lane_state(lane, snapshot)
        claim = latest_claim(events, lane_id)

        conductor_state, conductor_prov = conductor_claim_for_lane(lane, snapshot)

        if derived_state:
            state, evidence_class, provenance = derived_state, derived_ec, derived_prov
        elif claim:
            state, evidence_class, provenance = claim["payload"].get("state", "CLAIMED"), "CLAIMED", claim.get("provenance")
        elif conductor_state:
            state, evidence_class, provenance = conductor_state, "CLAIMED", conductor_prov
        else:
            # The honesty floor. This used to read PLANNED/"DERIVED" -- a fabricated status
            # dressed as evidence. 46 of 53 lanes have no observable artifact of any kind,
            # so PLANNED was a confident assertion the tracker had no basis for, and it is
            # precisely what let the board sit frozen through two shipped phases while
            # every liveness light stayed green. UNOBSERVABLE says the true thing: nothing
            # this tracker can see reports on this lane yet.
            state, evidence_class, provenance = (
                "UNOBSERVABLE", "UNKNOWN",
                "no merged-PR evidence, no branch, no artifact, no conductor entry for "
                f"{'/'.join(lane_identifiers(lane))}",
            )

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
            # Same matcher as derive_lane_state -- see find_lane_branch's docstring for
            # why two different rules here was itself a bug.
            "branch": find_lane_branch(lane, snapshot),
            "gate": lane.get("gate"),
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


DONE_STATES = {"MERGED", "CLOSED", "GATED"}
ACTIVE_STATES = {"BUILDING", "VERIFYING", "ADVERSARIAL", "QUEUED", "ADMISSIBLE", "SCOUTED"}


def fold_phase_status(plan, out_lanes, snapshot):
    """DERIVE each phase's status from its lanes' evidence, plus the conductor's gate
    results. Never a hand-typed constant again: PLAN.yaml used to carry `"status":
    "PLANNED"` string literals that the dashboard's phase rail rendered as if they were
    live state, so P1 and P2 both showed PLANNED for 17.5h after they had shipped -- P0
    showed CLOSED only because someone typed CLOSED."""
    by_phase = {}
    for lane in out_lanes:
        by_phase.setdefault(lane["phase"], []).append(lane)
    cs = (snapshot.get("conductor_state") or {})
    gates = ((cs.get("value") or {}).get("gate_results") or {}) if cs.get("evidence_class") == "DERIVED" else {}

    out = []
    for ph in plan["phases"]:
        lanes = by_phase.get(ph["id"], [])
        observable = [l for l in lanes if l["state"] != "UNOBSERVABLE"]
        done = [l for l in lanes if l["state"] in DONE_STATES]
        active = [l for l in lanes if l["state"] in ACTIVE_STATES]
        gate_id = ph.get("gate_id")
        gate_status = gates.get(gate_id) if gate_id else None

        if lanes and done and len(done) == len(lanes):
            status, why = "CLOSED", f"all {len(lanes)} lanes have merge evidence"
        elif gate_status == "PASSED" and done:
            status, why = ("CLOSED",
                           f"conductor reports {gate_id} PASSED and {len(done)}/{len(lanes)} lanes merged")
        elif active or done:
            status, why = ("ACTIVE",
                           f"{len(done)}/{len(lanes)} lanes merged, {len(active)} in flight")
        elif not observable:
            status, why = ("UNOBSERVABLE",
                           f"no evidence for any of this phase's {len(lanes)} lanes")
        else:
            status, why = "PLANNED", "no lane has started"
        entry = dict(ph)
        entry["status"] = status
        entry["status_provenance"] = why
        entry["lanes_total"] = len(lanes)
        entry["lanes_done"] = len(done)
        out.append(entry)
    return out


def board_world_divergence(out_lanes, snapshot, events, as_of_epoch):
    """The detector whose absence let this tracker sit frozen through two shipped phases
    while every liveness light stayed green.

    Observer freshness, ref freshness and subject progress all answer "is the OBSERVER
    working?". None of them answers "does what the board says match what the world did?".
    So: if merged PRs that this plan recognises have landed on main, but the board shows no
    lane for them as done, that is a contradiction between the tracker's own two eyes --
    and it is reported as an anomaly, not left for a human to notice 17 hours later."""
    merged = (snapshot.get("recent_merged_prs") or {}).get("value") or []
    if not merged:
        return {"checked": False, "reason": "no merged-PR evidence this cycle"}, []

    known = set()
    for lane in out_lanes:
        known.add(lane["id"].upper())
        if lane.get("gate"):
            known.add(lane["gate"].upper())
    done_idents = set()
    for lane in out_lanes:
        if lane["state"] in DONE_STATES:
            done_idents.add(lane["id"].upper())
            if lane.get("gate"):
                done_idents.add(lane["gate"].upper())

    unreflected = []
    for pr in merged:
        if not pr.get("is_ancestor_of_mirror_main"):
            continue
        implements = {i.upper() for i in (pr.get("implements") or [])}
        recognised = implements & known
        if recognised and not (recognised & done_idents):
            unreflected.append({"pr": pr["number"], "identifiers": sorted(recognised),
                                "title": pr.get("title", "")[:120]})

    summary = {
        "checked": True,
        "merged_prs_examined": len(merged),
        "unreflected_count": len(unreflected),
        "unreflected": unreflected[:10],
    }
    new_events = []
    for u in unreflected:
        key = f"pr{u['pr']}:{'+'.join(u['identifiers'])}"
        if any(e.get("kind") == "anomaly" and e.get("payload", {}).get("board_divergence_key") == key
               for e in events):
            continue
        new_events.append(dict(
            writer_id=PROJECTOR_WRITER_ID, kind="anomaly", lane=None,
            evidence_class="DERIVED",
            provenance="projector.py board-vs-world divergence check",
            payload={
                "message": f"PR #{u['pr']} merged to main implementing "
                           f"{', '.join(u['identifiers'])}, but no lane on this board shows "
                           f"it as done -- the board is behind the world.",
                "board_divergence_key": key, "pr_number": u["pr"],
                "identifiers": u["identifiers"],
            },
        ))
    return summary, new_events


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


def fold_code_provenance(snapshot):
    """An observatory that cannot tell you it is running old code is not trustworthy.
    Publishes what's ACTUALLY DEPLOYED (from INSTALLED_FROM.json, honestly UNKNOWN if the
    running install isn't a snapshot at all) so tracker.html can show it and flag staleness
    -- never silently trusted as current just because it's running."""
    cp = snapshot.get("code_provenance") or {}
    if cp.get("evidence_class") != "DERIVED":
        return {
            "evidence_class": cp.get("evidence_class", "UNKNOWN"),
            "provenance": cp.get("provenance"),
            "code_sha": None, "code_sha_short": None, "code_installed_at": None,
            "code_source_ref": None, "code_is_current": None, "code_stale": None,
            "code_is_ancestor_of_main": None, "code_state": None, "code_behind_count": None,
        }
    v = cp["value"]
    installed = v.get("installed", {})
    sha = installed.get("source_sha")
    # Item 1a: CURRENT/AHEAD/BEHIND/DIVERGED, not a binary is_current -- an unmerged sha
    # that's ahead of main (e.g. deployed pre-merge for live verification, exactly this
    # PR's own workflow) used to render the same amber "STALE CODE" as a genuinely stale
    # one. Only BEHIND/DIVERGED are amber now.
    state = classify_code_provenance(v.get("is_ancestor_of_origin_main"), v.get("contains_latest_tracker_commit"))
    return {
        "evidence_class": "DERIVED", "provenance": cp.get("provenance"),
        "code_sha": sha, "code_sha_short": (sha[:10] if sha else None),
        "code_installed_at": installed.get("installed_at"),
        "code_source_ref": installed.get("source_ref"),
        "code_is_current": v.get("is_current"),
        "code_stale": state in ("BEHIND", "DIVERGED"),
        "code_is_ancestor_of_main": v.get("is_ancestor_of_origin_main"),
        "code_state": state,
        "code_behind_count": v.get("behind_count"),
        "latest_tracker_subtree_commit_on_main": v.get("latest_tracker_subtree_commit_on_main"),
    }


def fold_ref_freshness(snapshot):
    """The THIRD liveness axis (CLAUDE.md-adjacent §N.8 applied to the instrument):
    observer freshness (is the tracker alive), subject progress (is the swarm moving), and
    THIS (are the refs the tracker reasons from actually current) are independent -- a
    green observer over stale refs is exactly the silently-stale-looking-fresh failure
    this axis exists to catch. Published directly from the collector's mirror_fetch result
    (not folded from events -- it's already a per-cycle collector signal, same pattern as
    github_rate_limit)."""
    mf = snapshot.get("mirror_fetch") or {}
    return {
        "last_fetch_ok": mf.get("ok"),
        "last_fetch_ts": mf.get("ts"),
        "last_fetch_action": mf.get("action"),
        "last_fetch_duration_ms": mf.get("duration_ms"),
        "last_fetch_error": mf.get("error"),
        "last_success_ts": mf.get("last_success_ts"),
        "consecutive_failures": mf.get("consecutive_failures", 0),
    }


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
    new_events = new_events + gh_mirror_anomalies(snapshot, events)
    divergence, divergence_events = board_world_divergence(out_lanes, snapshot, events, as_of_epoch)
    new_events = new_events + divergence_events

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

    derived_phases = fold_phase_status(plan, out_lanes, snapshot)
    current_phase = next((p for p in derived_phases if p["status"] not in ("CLOSED",)), derived_phases[-1])

    heartbeat = {}
    if os.path.exists(HEARTBEAT_JSON):
        try:
            with open(HEARTBEAT_JSON, encoding="utf-8") as f:
                heartbeat = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            heartbeat = {}

    # Item (d): sticky, survives-restarts record, distinct from the anomalies feed above
    # (which is a rolling window). This one stays until tracker-ack-blind clears
    # `acknowledged`, so the banner it drives cannot be laundered away by the mere act of
    # the daemon coming back up green.
    blind_window = None
    if os.path.exists(BLIND_WINDOW_JSON):
        try:
            with open(BLIND_WINDOW_JSON, encoding="utf-8") as f:
                blind_window = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            blind_window = None

    state = {
        "schema_version": "2.0",
        "generated_at": generated_at,
        "plan_version": plan["plan_version"],
        "current_phase": current_phase["id"],
        "phases": derived_phases,
        "lanes": out_lanes,
        "critical_path": {"path": path, "blocking_lane": blocking_lane},
        "anomalies": [
            {"ts": a["ts"], "lane": a.get("lane"), "message": a["payload"].get("message")}
            for a in anomalies
        ],
        "blind_window": blind_window,
        "budget": fold_budget(plan, events),
        "code_provenance": fold_code_provenance(snapshot),
        "ref_freshness": fold_ref_freshness(snapshot),
        "board_world_divergence": divergence,
        "conductor_state": snapshot.get("conductor_state"),
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
