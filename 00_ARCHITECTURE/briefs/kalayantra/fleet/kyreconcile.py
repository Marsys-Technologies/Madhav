#!/usr/bin/env python3
"""KĀLA-YANTRA v3 plan-model reconciliation (relaunch plan v2.2 §0 steps 3–5, §6 item declaration, §14 B-0b).

Deterministic and offline: it reads files and writes only the files named on its command line. It never talks to
the tracker and never writes an event. Two stages, kept apart so that each has its own reconciliation test:

  stage P — path-only migration: the old campaign checkout path becomes the policy-root campaign checkout and
            every stream's worktree list is re-derived for the one-worktree-per-item topology (plan §5).
            Nothing else changes; item states computed from the same events, detector results and clock are identical.
  stage T — triage: the declared edits of TRIAGE_DECLARATIONS (retirement decisions, re-cut dependencies, schema
            prerequisites, declaration fields, triage classes, regenerated close join, coverage ids).

  kyreconcile.py build    --base B --declarations D --roots R --out MODEL
  kyreconcile.py check    --base B --declarations D --roots R --model MODEL      exit 1 if MODEL is not the build
  kyreconcile.py capture  --state STATE.json --base B --events EVENTS --out CAPTURE.json
  kyreconcile.py delta    --base B --model MODEL --declarations D --staged S --capture C --events EVENTS --out DELTA
  kyreconcile.py priority --model MODEL --capture C --out PRIORITY.txt
  kyreconcile.py report   --model MODEL --declarations D --closure CL --capture C --schema SR --delta DELTA --out TRIAGE.md

B may be plain JSON or .json.gz (the checked-in pre-reconciliation fixture).
"""
from __future__ import annotations

import argparse
import collections
import copy
import datetime as dt
import gzip
import hashlib
import json
import re
import sys
from pathlib import Path

FLEET = Path(__file__).resolve().parent
REPO = FLEET.parents[3]
sys.path.insert(0, str(FLEET))

import kyclosure  # noqa: E402

POLICY_ROOT = "/Users/Dev/worktrees.noindex/madhav/claude"
CAMPAIGN = POLICY_ROOT + "/kalayantra-campaign"
OLD_CAMPAIGN = "/Users/Dev/kalayantra/wt/campaign"
PATH_MAP = ((OLD_CAMPAIGN, CAMPAIGN),)
MODEL_VERSION_SUFFIX = "+v3-reconcile-20261011"
OLD_NOTE = "(branch campaign/kalayantra until B-1 merges; origin/main after B-2)"
NEW_NOTE = "(branch kalayantra/campaign, upstream origin/main; the checkout is created by the v3 B-2 installation)"
DELTA_SCHEMA = "kalayantra.triage_delta/1"
CAPTURE_SCHEMA = "kalayantra.reconcile_capture/1"
STATE_KEYS = ("status", "source", "detail", "progress", "evidence", "steps", "deps_open", "deps_open_strict",
              "deps_merged_pending_deploy", "skip_origin", "gaps", "outcome", "detector_warning", "started_at",
              "updated_at", "checked_at")
READINESS_KEYS = ("status", "deps_open", "deps_open_strict", "skip_origin", "gaps")
DECLARATION_KEYS = ("completion_kind", "producer", "reviewer_rule", "step_evidence", "triage")
# detector details that the tracker's detectors report with status `running` (detectors.py)
DETECTOR_RUNNING = (r"commits on \S+ not yet on main$", r"^PR #\d+ open \(", r"exists but is only \d+ bytes$")
STEP_EVIDENCE = {"code": "pr_head_evidence", "artifact": "artifact_section", "operation": "executor_receipt",
                 "packet": "review_record"}
LEGEND = {
    "plan": "KALAYANTRA_RELAUNCH_PLAN_v2_2.md §6 (item declaration); written by fleet/kyreconcile.py, never by hand",
    "applies_to": "every executable item (one that is not completed by a decision or a join)",
    "completion_kind": {
        "code": "a merged pull request: independent verdict at the exact reviewed head, then the squash merge commit",
        "artifact": "a registered artifact: path + SHA-256, independently accepted at that digest",
        "operation": "an executor operation: request and operation identity, completed receipt, independent readback",
        "packet": "a packet-exit review: verdict bound to the reviewed packet and its review digest"},
    "producer": "the stream that produces the item's evidence (the item's owner); only that stream claims the item",
    "reviewer_rule": {
        "v_exact_head_then_deploy_containment": "V verdict at the exact PR head by a slot independent of the author; complete once a successful deployment of main contains the squash merge commit",
        "v_exact_head_then_post_deploy_at_merge_commit": "V verdict at the exact PR head, then a second V verdict (post_deploy) at the squash merge commit with the migration or operation readback",
        "v_artifact_digest_reviewer_not_author": "V verdict bound to the artifact's SHA-256; the reviewer slot differs from the recorded author identity; a V claim only when the item is V-owned",
        "finalizer_independent_review_artifact_digest": "the finalizer's bounded independent reviewer accepts the receipt's exact digest (plan §12), outside ordinary dispatch",
        "v_pre_acceptance_then_receipt_readback_digest": "independent V pre-acceptance of the request, then V acceptance of the completed receipt's digest after measured readback",
        "v_packet_verdict_bound_to_external_review": "V packet verdict with no open blocking finding, bound to the review record's digest"},
    "step_evidence": "per required step: the evidence class the step must cite and its named detector. detector null = not yet named: the item's packet names it; a STEP action never records a step whose detector is null or has not passed (CLAUDE.md §N.8)",
    "earned": "for an item already completed, completion_kind is the type recorded in its guarded completion event",
    "triage": "class a = critical path (closure of acceptances i–iii); a_close = the close chain (acceptance iv); b = deferred with a re-entry condition, never counted as closed; c = dispositioned under J0_DISPOSITION; retired / retire_decision = retirement by decision (refusal staged, published only by B-2); done_outside = earned completion outside the closure, preserved",
}


# ---------------------------------------------------------------- files

def load(path) -> dict:
    p = Path(path)
    raw = gzip.decompress(p.read_bytes()) if p.suffix == ".gz" else p.read_bytes()
    return json.loads(raw.decode("utf-8"))


def render(obj) -> bytes:
    """the repository's formatting of the plan model: two-space indent, UTF-8, one trailing newline"""
    return (json.dumps(obj, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


digest = kyclosure.digest


# ---------------------------------------------------------------- shared predicates

def executable(item: dict) -> bool:
    return (item.get("done_by") not in ("decision", "join") and item.get("join") is not True
            and bool(item.get("detector")))


def writes_data(item: dict) -> bool:
    """same rule as the tracker's completion.writes_data"""
    brief = item.get("brief") if isinstance(item.get("brief"), dict) else {}
    return bool(brief.get("migration")) or bool(brief.get("op"))


def item_worktree(item_id: str) -> str:
    return f"{POLICY_ROOT}/kalayantra-{item_id.lower()}"


def _map_strings(obj, fn):
    if isinstance(obj, str):
        return fn(obj)
    if isinstance(obj, list):
        return [_map_strings(x, fn) for x in obj]
    if isinstance(obj, dict):
        return {k: _map_strings(v, fn) for k, v in obj.items()}
    return obj


def assign_worktrees(model: dict) -> None:
    """S and N work in the campaign checkout and their own item worktrees; K in its item worktrees; V reviews in
    the item's worktree under the item lock, so it lists every item worktree (plan §5)."""
    own = collections.defaultdict(list)
    every = []
    for it in model["items"]:
        if executable(it):
            own[it["owner"]].append(item_worktree(it["id"]))
            every.append(item_worktree(it["id"]))
    for s in model["streams"]:
        s["worktrees"] = [CAMPAIGN] + (every if s["id"] == "V" else own.get(s["id"], []))


# ---------------------------------------------------------------- stage P

def migrate_paths(base: dict) -> dict:
    def fn(s: str) -> str:
        for old, new in PATH_MAP:
            s = s.replace(old, new)
        return s
    m = _map_strings(copy.deepcopy(base), fn)
    assign_worktrees(m)
    return m


def unmigrate_paths(migrated: dict, base: dict) -> dict:
    """inverse of stage P given the base stream worktree lists; used to prove the stage changed paths only"""
    def fn(s: str) -> str:
        for old, new in PATH_MAP:
            s = s.replace(new, old)
        return s
    m = _map_strings(copy.deepcopy(migrated), fn)
    for s, b in zip(m["streams"], base["streams"]):
        s["worktrees"] = list(b["worktrees"])
    return m


# ---------------------------------------------------------------- stage T

def completion_kind(item: dict, decl: dict) -> str:
    iid = item["id"]
    earned = decl["earned_completion_kinds"]["kinds"]
    if iid in earned:
        return earned[iid]
    if iid in decl["completion_kind_overrides"]:
        return decl["completion_kind_overrides"][iid]
    det = item.get("detector") or {}
    path = det.get("path", "")
    if iid.startswith("V-") and path.endswith(".VERDICT.json"):
        return "packet"
    if det.get("type") in ("branch_merged", "pr_merged"):
        return "code"
    if item["owner"] == "N" and (item["brief"].get("op") or "/run/ops/receipts/" in path
                                 or det.get("type") == "db_query"):
        return "operation"
    if det.get("type") == "file_contains" and path.endswith("/fleet/executor_ops.json"):
        return "code"
    return "artifact"


def reviewer_rule(item: dict, kind: str) -> str:
    if kind == "code":
        return ("v_exact_head_then_post_deploy_at_merge_commit" if writes_data(item)
                else "v_exact_head_then_deploy_containment")
    if kind == "operation":
        return "v_pre_acceptance_then_receipt_readback_digest"
    if kind == "packet":
        return "v_packet_verdict_bound_to_external_review"
    if item["id"] in ("C-3", "C-4"):
        return "finalizer_independent_review_artifact_digest"
    return "v_artifact_digest_reviewer_not_author"


def root_ids(roots: dict) -> list:
    return sorted({r["item"] for a in roots["acceptances"] for r in a["roots"]})


def apply_triage(pmodel: dict, decl: dict, roots: dict) -> dict:
    m = copy.deepcopy(pmodel)
    items = m["items"]
    ix = {i["id"]: i for i in items}

    # 1. retirement by decision (plan §0 step 4): decision registered, the item requires `approved`
    retired, retire_decisions = {}, {}
    for d in decl["retire_decisions"]:
        if d["id"] in ix or any(x["id"] == d["id"] for x in m["decisions"]):
            raise ValueError(f"{d['id']} is already in the model")
        m["decisions"].append(copy.deepcopy(d["record"]))
        items.append(copy.deepcopy(d["item"]))
        tgt = ix[d["retires"]]
        tgt["depends_on"] = sorted(set(tgt["depends_on"]) | {d["id"]})
        tgt["requires_outcome"] = {**tgt.get("requires_outcome", {}), d["id"]: "approved"}
        retired[d["retires"]] = d["id"]
        retire_decisions[d["id"]] = d["retires"]

    # 2. re-cut dependencies (owner decision)
    for r in decl["recuts"]:
        tgt = ix[r["item"]]
        if sorted(tgt["depends_on"]) != sorted(r["replaces"]):
            raise ValueError(f"{r['item']}: dependencies are {tgt['depends_on']}, the re-cut expects {r['replaces']}")
        tgt["depends_on"] = list(r["depends_on"])

    # 3. schema prerequisites (plan §0 step 3): a new item; its consumer waits for it
    for sp in decl["schema_prerequisites"]:
        if sp["id"] in ix:
            raise ValueError(f"{sp['id']} is already in the model")
        items.append(copy.deepcopy(sp["item"]))
        consumer = ix[sp["consumer"]]
        consumer["depends_on"] = sorted(set(consumer["depends_on"]) | {sp["id"]})
    ix = {i["id"]: i for i in items}

    # 4. topology that is not a path: branch patterns, the documents note, worktrees of new items
    for s in m["streams"]:
        add = decl["branch_pattern_additions"].get(s["id"])
        if add:
            if not s["branch_pattern"].startswith("^("):
                raise ValueError(f"stream {s['id']}: unexpected branch pattern")
            s["branch_pattern"] = "^(" + add + "|" + s["branch_pattern"][2:]
    note = m["documents"]["_note"]
    if OLD_NOTE not in note:
        raise ValueError("documents._note does not carry the expected branch sentence")
    m["documents"]["_note"] = note.replace(OLD_NOTE, NEW_NOTE)
    assign_worktrees(m)

    # 5. coverage: ids folded by the v2.0 regroup; definition-of-done line 4
    idmap = decl["coverage_id_map"]

    def remap(lst):
        out = []
        for x in lst:
            y = idmap.get(x, x)
            if y not in out:
                out.append(y)
        return out
    for section in m["coverage"].values():
        for key in list(section):
            section[key] = remap(section[key])
    dod = m["coverage"]["definition_of_done"]
    line4 = [k for k in dod if k.startswith("line 4")]
    if len(line4) != 1:
        raise ValueError("definition_of_done has no single line 4")
    dod[line4[0]] = list(decl["definition_of_done_line4"])
    dangling = sorted({x for sec in m["coverage"].values() for lst in sec.values() for x in lst if x not in ix})
    if dangling:
        raise ValueError(f"coverage names ids that are not in the model: {dangling}")

    # 6. triage classes from the closure of the acceptance roots
    graph = {i["id"]: i for i in items}
    closure = kyclosure.reach(graph, root_ids(roots))
    chain = list(roots["mechanical_close_chain"]["items"])
    declared = (set(decl["deferred"]) | set(decl["dispositioned"]) | set(retired) | set(retire_decisions)
                | set(decl["done_outside"]) | set(chain))
    clash = sorted(declared & closure)
    if clash:
        raise ValueError(f"declared outside the critical path but in the closure: {clash}")

    def triage(iid):
        if iid in closure:
            return {"class": "a"}
        if iid in chain:
            return {"class": "a_close"}
        if iid in retired:
            return {"class": "retired", "decision": retired[iid]}
        if iid in retire_decisions:
            return {"class": "retire_decision", "retires": retire_decisions[iid]}
        if iid in decl["deferred"]:
            return {"class": "b", **decl["deferred"][iid]}
        if iid in decl["dispositioned"]:
            return {"class": "c", **decl["dispositioned"][iid]}
        if iid in decl["done_outside"]:
            return {"class": "done_outside"}
        raise ValueError(f"{iid} is outside the closure and has no declared disposition")

    # 7. declaration fields (plan §6)
    for it in items:
        if executable(it):
            kind = completion_kind(it, decl)
            it["completion_kind"] = kind
            it["producer"] = it["owner"]
            it["reviewer_rule"] = reviewer_rule(it, kind)
            if it.get("steps"):
                it["step_evidence"] = {s: {"evidence": STEP_EVIDENCE[kind], "detector": None} for s in it["steps"]}
        it["triage"] = triage(it["id"])

    # 8. joins and the close chain, regenerated from the retained set
    cls = {i["id"]: i["triage"]["class"] for i in items}
    for it in items:
        if it["id"] == "JOIN-ALL" or cls[it["id"]] == "b":
            continue
        on_b = [d for d in it.get("depends_on", []) if cls[d] == "b"]
        if on_b:
            raise ValueError(f"{it['id']} is retained but depends on deferred {on_b}")
    join = ix["JOIN-ALL"]
    join["depends_on"] = sorted(i for i, c in cls.items() if c not in ("b", "a_close"))
    join["title"] = ("Retained-results join (relaunch plan v2.2 §0): every retained item is terminal (done, or "
                     "not_applicable with its reason); the mandatory items that ended not_applicable are listed as "
                     "the campaign's gaps; the deferred items are listed with their re-entry conditions and are "
                     "never counted as closed")
    join["brief"]["tests"] = list(join["brief"]["tests"]) + [
        "the deferred list equals the model's triage class b set, each with its re-entry condition"]
    close = ix["C-1"]
    close["brief"]["tests"] = list(close["brief"]["tests"]) + [
        "the deferred (class b) list with re-entry conditions is attached; a deferred item is never reported closed"]

    # 9. the model's own description of these fields
    m["control_plane"]["declarations"] = copy.deepcopy(LEGEND)
    m["control_plane"]["triage"] = {
        "plan": "00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_2.md §0",
        "roots": "00_ARCHITECTURE/control/kalayantra/ACCEPTANCE_ROOTS_v2_1.json",
        "closure": "00_ARCHITECTURE/control/kalayantra/CLOSURE_v2_1.json",
        "declarations": "00_ARCHITECTURE/control/kalayantra/TRIAGE_DECLARATIONS_v2_2.json",
        "staged_actions": "00_ARCHITECTURE/control/kalayantra/STAGED_MODEL_ACTIONS_v2_2.json (not published; B-2 publishes)",
        "schema_receipt": "00_ARCHITECTURE/control/kalayantra/SCHEMA_RECEIPT_v2_2.json",
        "generator": "00_ARCHITECTURE/briefs/kalayantra/fleet/kyreconcile.py build",
    }
    m["model_version"] = m["model_version"] + MODEL_VERSION_SUFFIX
    return m


def build(base: dict, decl: dict, roots: dict) -> dict:
    return apply_triage(migrate_paths(base), decl, roots)


# ---------------------------------------------------------------- tracker replay (pure functions of the tracker source)

def _tracker():
    gov = str(REPO / "platform" / "scripts" / "governance")
    if gov not in sys.path:
        sys.path.insert(0, gov)
    from pravaha_tracker import state  # noqa: PLC0415
    return state


def read_events_prefix(path, capture: dict) -> list:
    """the first `bytes` bytes of the append-only event log; refuses a prefix whose hash differs from the capture"""
    want = capture["events"]
    with open(path, "rb") as f:
        raw = f.read(want["bytes"])
    if len(raw) != want["bytes"] or sha256_bytes(raw) != want["sha256"]:
        raise ValueError(f"{path}: the first {want['bytes']} bytes do not hash to {want['sha256']}")
    return [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]


def states(model: dict, events: list, capture: dict, keys=STATE_KEYS) -> dict:
    state = _tracker()
    now = dt.datetime.fromisoformat(capture["clock"])
    snap = state.build_snapshot(model, events, capture["detector_results"], {}, {}, {}, now)
    return {row["id"]: {k: row[k] for k in keys if k in row} for tr in snap["tracks"] for row in tr["items"]}


def make_capture(state_json: dict, base: dict, events_path: str) -> dict:
    """One detector-result map and one clock from a saved GET /api/state. The tracker does not expose raw detector
    results, so each result is reduced to {status, checked_at}: `done` where the snapshot shows the detector
    matched, `running` where its detail is one the detectors report as in flight, `pending` otherwise. The reduction is validated by replay (see `replay_mismatches`)."""
    rows = {i["id"]: i for t in state_json["tracks"] for i in t["items"]}
    det = {}
    for it in base["items"]:
        row = rows[it["id"]]
        if not it.get("detector") or not row.get("checked_at"):
            continue
        detail = row.get("detail") or ""
        matched = ((row.get("source") == "guarded:event" and "detector_warning" not in row)
                   or detail.startswith("detector matched; guarded completion pending"))
        tail = detail.rsplit(" · ", 1)[-1]
        in_flight = any(re.search(rx, tail) for rx in DETECTOR_RUNNING)
        det[it["id"]] = {"status": "done" if matched else "running" if in_flight else "pending", "detail": "",
                         "checked_at": row["checked_at"]}
    raw = Path(events_path).read_bytes()
    return {
        "schema": CAPTURE_SCHEMA,
        "source": f"tracker GET /api/state, version {state_json.get('version')}, generated_at {state_json['generated_at']}",
        "clock": state_json["generated_at"],
        "events": {"default_path": str(events_path), "bytes": len(raw), "lines": raw.count(b"\n"),
                   "sha256": sha256_bytes(raw)},
        "detector_results": det,
        "detector_results_note": "reduced to {status, checked_at}; `detail` is not recoverable from the snapshot and is empty",
        "item_states": {iid: {k: row[k] for k in ("status", "deps_open", "deps_open_strict") if k in row}
                        for iid, row in sorted(rows.items())},
    }


def replay_mismatches(base: dict, events: list, capture: dict) -> dict:
    got = states(base, events, capture, keys=("status", "deps_open", "deps_open_strict"))
    return {iid: {"captured": want, "replayed": got.get(iid)}
            for iid, want in capture["item_states"].items() if got.get(iid) != want}


# ---------------------------------------------------------------- the triage delta

def _dep_delta(a: dict, b: dict) -> dict:
    out = {}
    da, db = a.get("depends_on", []), b.get("depends_on", [])
    if sorted(da) != sorted(db):
        out["depends_on"] = {"added": sorted(set(db) - set(da)), "removed": sorted(set(da) - set(db))}
    ra, rb = a.get("requires_outcome") or {}, b.get("requires_outcome") or {}
    if ra != rb:
        out["requires_outcome"] = {"added": {k: v for k, v in rb.items() if ra.get(k) != v},
                                   "removed": {k: v for k, v in ra.items() if rb.get(k) != v}}
    return out


def staged_events(staged: dict, clock: str) -> list:
    """the events B-2 would publish for the staged actions — built in memory for simulation, never written"""
    note = "SIMULATED — staged, not published"
    out = [{"ts": clock, "kind": "decision", "decision": d["decision"], "state": "delegated",
            "outcome": d["outcome"], "actor": d["as"], "detail": note} for d in staged["decisions"]]
    for state, key in (("parked", "parks"), ("blocked", "blocks")):
        out += [{"ts": clock, "kind": "item", "item": x["item"], "state": state, "actor": x["as"], "detail": note}
                for x in staged.get(key, [])]
    return out


def _readiness(before: dict | None, after: dict) -> dict:
    """status before/after; open-dependency lists as added/removed (in full for an item that did not exist)"""
    if before is None:
        return {"new_item": True, **after}
    out = {"status": [before["status"], after["status"]]}
    for k in ("deps_open", "deps_open_strict"):
        a, b = before.get(k) or [], after.get(k) or []
        if a != b:
            out[k] = {"added": sorted(set(b) - set(a)), "removed": sorted(set(a) - set(b)), "count": [len(a), len(b)]}
    for k in ("skip_origin", "gaps"):
        if before.get(k) != after.get(k):
            out[k] = [before.get(k), after.get(k)]
    return out


def compute_delta(base: dict, final: dict, decl: dict, staged: dict, capture: dict, events: list) -> dict:
    p = migrate_paths(base)
    pi, fi = {i["id"]: i for i in p["items"]}, {i["id"]: i for i in final["items"]}
    added = [i for i in fi if i not in pi]
    if [i for i in pi if i not in fi]:
        raise ValueError("an item was removed; the reconciliation never removes an item")

    dependencies, other = {}, {}
    for iid in pi:
        dd = _dep_delta(pi[iid], fi[iid])
        # the regenerated close join is reported under close_membership, in full
        if dd and iid != "JOIN-ALL":
            dependencies[iid] = dd
        skip = set(DECLARATION_KEYS) | {"depends_on", "requires_outcome"}
        ch = {k: [pi[iid].get(k), fi[iid].get(k)] for k in sorted(set(pi[iid]) | set(fi[iid]))
              if k not in skip and pi[iid].get(k) != fi[iid].get(k)}
        if ch:
            other[iid] = ch

    top = {}
    for k in sorted(set(p) | set(final)):
        if k in ("items", "streams") or p.get(k) == final.get(k):
            continue
        if isinstance(p.get(k), dict) and isinstance(final.get(k), dict):
            top[k] = {kk: [p[k].get(kk), final[k].get(kk)] for kk in sorted(set(p[k]) | set(final[k]))
                      if p[k].get(kk) != final[k].get(kk)}
        elif isinstance(p.get(k), list) and isinstance(final.get(k), list):
            top[k] = {"added": [x for x in final[k] if x not in p[k]], "removed": [x for x in p[k] if x not in final[k]]}
        else:
            top[k] = [p.get(k), final.get(k)]
    streams = {}
    for a, b in zip(p["streams"], final["streams"]):
        ch = {k: [a.get(k), b.get(k)] for k in sorted(set(a) | set(b)) if k != "worktrees" and a.get(k) != b.get(k)}
        wa, wb = a["worktrees"], b["worktrees"]
        if wa != wb:
            ch["worktrees"] = {"added": [w for w in wb if w not in wa], "removed": [w for w in wa if w not in wb]}
        if ch:
            streams[a["id"]] = ch

    before = states(p, events, capture)
    after = states(final, events, capture)
    pick = lambda st, iid: {k: st[iid].get(k) for k in READINESS_KEYS}  # noqa: E731
    readiness = {}
    for iid in fi:
        b = pick(before, iid) if iid in before else None
        a = pick(after, iid)
        if a != b:
            readiness[iid] = _readiness(b, a)
    earned_before = {i: s for i, s in before.items() if s["status"] == "done"}
    earned = {i: {"evidence_sha256": sha256_bytes(json.dumps(s.get("evidence"), ensure_ascii=False).encode()),
                  "source": s.get("source"),
                  "unchanged": after[i]["status"] == "done" and after[i].get("evidence") == s.get("evidence")
                  and after[i].get("source") == s.get("source")}
              for i, s in sorted(earned_before.items())}

    sim = states(final, events + staged_events(staged, capture["clock"]), capture)
    staged_effects = {iid: _readiness(pick(after, iid), pick(sim, iid)) for iid in fi if pick(sim, iid) != pick(after, iid)}

    ja, jb = pi["JOIN-ALL"]["depends_on"], fi["JOIN-ALL"]["depends_on"]
    classes = collections.Counter(i["triage"]["class"] for i in final["items"])
    out = {
        "schema": DELTA_SCHEMA,
        "plan": "KALAYANTRA_RELAUNCH_PLAN_v2_2.md §0 step 5 (triage reconciliation: dependencies, dispositions, readiness, close membership, earned completions)",
        "inputs": {
            "base_model_canonical_sha256": digest(base),
            "path_migrated_model_canonical_sha256": digest(p),
            "declarations_canonical_sha256": digest(decl),
            "staged_actions_canonical_sha256": digest(staged),
            "events_prefix": capture["events"],
            "clock": capture["clock"],
            "detector_results_canonical_sha256": digest(capture["detector_results"]),
        },
        "counts": {"items_before": len(pi), "items_after": len(fi), "classes": dict(sorted(classes.items())),
                   "status_before": dict(sorted(collections.Counter(s["status"] for s in before.values()).items())),
                   "status_after": dict(sorted(collections.Counter(s["status"] for s in after.values()).items()))},
        "items_added": [fi[i] for i in added],
        "decisions_added": [d for d in final["decisions"] if d not in p["decisions"]],
        "dependencies": dependencies,
        "dispositions": {i["id"]: i["triage"] for i in final["items"]},
        "declarations": {i["id"]: {"completion_kind": i["completion_kind"], "producer": i["producer"],
                                   "reviewer_rule": i["reviewer_rule"], "steps": list(i.get("step_evidence", {})),
                                   "step_evidence_classes": sorted({v["evidence"] for v in i.get("step_evidence", {}).values()}),
                                   "step_detectors_named": sum(1 for v in i.get("step_evidence", {}).values() if v["detector"])}
                         for i in final["items"] if "completion_kind" in i},
        "other_item_changes": other,
        "topology": {"model": top, "streams": streams},
        "readiness": readiness,
        "close_membership": {"join": "JOIN-ALL", "before": len(ja), "after": len(jb),
                             "added": sorted(set(jb) - set(ja)), "removed": sorted(set(ja) - set(jb)),
                             "members": list(jb),
                             "close_chain": {i: fi[i]["depends_on"] for i in ("C-1", "C-2", "C-3", "C-4")}},
        "earned_completions": {"count": len(earned), "all_unchanged": all(v["unchanged"] for v in earned.values()),
                               "items": earned},
        "staged_effects_if_published": staged_effects,
    }
    return out


# ---------------------------------------------------------------- priority and report

WAVE0 = ["J-0c", "J-0d", "J-0m", "J-4p", "K4-2a", "K4-2aw", "K4-2b", "K4-3", "K6-5a", "K6-5", "K6-123",
         "K7-1a", "K7-1b", "K7-2", "K-CERT-2", "K7-3"]


def priority_lines(model: dict, capture: dict) -> list:
    """BUILD admission order: Wave 0 as the plan §14 lists it, then every other open executable critical-path
    item in dependency order (ties in model order), then the dispositioned items and the close chain."""
    ix = {i["id"]: i for i in model["items"]}
    st = capture["item_states"]
    open_ = lambda i: st.get(i, {}).get("status") != "done"  # noqa: E731
    cls = {i: x["triage"]["class"] for i, x in ix.items()}
    order, seen = [], set()

    def visit(i):
        if i in seen:
            return
        seen.add(i)
        for d in ix[i].get("depends_on", []):
            visit(d)
        order.append(i)
    for i in WAVE0:
        if i not in ix:
            raise ValueError(f"Wave 0 names {i}, which is not in the model")
    wave0 = [i for i in WAVE0 if open_(i)]
    seen.update(wave0)
    for i in ix:
        if cls[i] == "a":
            visit(i)
    wave1 = [i for i in order if executable(ix[i]) and open_(i) and cls[i] == "a"]
    tail = [i for i in ix if cls[i] == "c" and executable(ix[i]) and open_(i)]
    chain = [i for i in ix if cls[i] == "a_close" and executable(ix[i])]
    out = ["# KĀLA-YANTRA v3 BUILD priority — generated by fleet/kyreconcile.py priority; do not edit by hand",
           f"# model {model['model_version']} (canonical sha256 {digest(model)})",
           f"# statuses: {capture['source']}",
           "# one item id per line; deferred (b) and retired items are absent by construction",
           "# wave 0 (plan §14)"] + wave0 + ["# wave 1+ — critical path in dependency order"] + wave1 \
        + ["# dispositioned (c)"] + tail + ["# close chain"] + chain
    return out


def report(model, decl, closure, capture, schema, delta, hashes) -> str:
    ix = {x["id"]: x for x in model["items"]}
    s = capture["item_states"]
    status = lambda i: s.get(i, {}).get("status") or delta["readiness"].get(i, {}).get("status", "new")  # noqa: E731
    cls = {i: x["triage"]["class"] for i, x in ix.items()}
    cnt = collections.Counter(cls.values())
    done = lambda c: sum(1 for i, k in cls.items() if k == c and status(i) == "done")  # noqa: E731
    open_a = [i for i, k in cls.items() if k == "a" and status(i) != "done"]
    by = collections.Counter(status(i) for i in open_a)
    label = {"a": "a", "a_close": "a·close", "b": "b", "c": "c", "retired": "retired",
             "retire_decision": "retire-decision", "done_outside": "done·outside"}

    def cite(x):
        sp = x["brief"].get("spec") or []
        t = "; ".join(sp[:2]) if isinstance(sp, list) else str(sp)
        return (t[:88] + "…") if len(t) > 88 else t
    o = []
    w = o.append
    w(f"""---
artifact: KALAYANTRA_V3_TRIAGE_v2_2.md
content_version: 2.2
status: {hashes['status']}
authored_by: Claude Code (Opus 5.5, xhigh) — KĀLA-YANTRA v3 Planner, sessions local_ec1c912e-e039-4666-abc3-a815f9c4a2d1 (draft) and local_ef70d1f5-345a-4255-847f-212971af5951 (reconciliation)
plan: KALAYANTRA_RELAUNCH_PLAN_v2_2.md §0 steps 3–5
inputs:
  model: 00_ARCHITECTURE/control/kalayantra/plan_model.json ({len(ix)} items; canonical sha256 {closure['inputs']['model_canonical_sha256']})
  roots: 00_ARCHITECTURE/control/kalayantra/ACCEPTANCE_ROOTS_v2_1.json (canonical sha256 {closure['inputs']['roots_canonical_sha256']})
  closure: 00_ARCHITECTURE/control/kalayantra/CLOSURE_v2_1.json (file sha256 {hashes['closure_file']}; content hash {closure['closure_sha256']})
  declarations: 00_ARCHITECTURE/control/kalayantra/TRIAGE_DECLARATIONS_v2_2.json (file sha256 {hashes['declarations_file']})
  expected_delta: 00_ARCHITECTURE/control/kalayantra/TRIAGE_EXPECTED_DELTA_v2_2.json (file sha256 {hashes['delta_file']})
  schema_receipt: 00_ARCHITECTURE/control/kalayantra/SCHEMA_RECEIPT_v2_2.json ({schema['schema_receipt_id']})
  live_status: {capture['source']}; EVENTS.jsonl {capture['events']['lines']} lines, sha256 {capture['events']['sha256']}
owner_decisions: 2026-10-11 — closure accepted as computed with no root or edge cut; J-7a and B-DB-BASELINE deferred; J-8a and J-8 dispositioned with J-8a re-cut to J-0 + V-J6; roots V-K9, K-AVADHI-C (i) and K-CERT, K-CERT-2 (iii) confirmed (WORKTREE_DISPOSITIONS_v2_1.md §6; run/HANDOFF_PLANNER_20261011T141551Z.md)
review: {hashes['review']}
generator: fleet/kyreconcile.py report (deterministic; the tables are not hand-edited)
---

# KĀLA-YANTRA v3 — triage of the {len(ix)} plan-model items

## 1. Result

| class | meaning | items | of which already done |
|---|---|--:|--:|
| (a) critical path | in the closure of acceptances (i)–(iii) | {cnt['a']} | {done('a')} |
| (a·close) | the mechanical close chain for acceptance (iv); regenerated from the retained set, not a scope root | {cnt['a_close']} | 0 |
| (b) deferred | parked with a re-entry condition; never counted as closed | {cnt['b']} | 0 |
| (c) dispositioned | inherited Pravāha material under the accepted J0_DISPOSITION | {cnt['c']} | 0 |
| retired by decision | unfinished control-plane items; refusal staged, published only by B-2 | {cnt['retired']} | 0 |
| retirement decisions | the two D-RETIRE-* decision items registered for them | {cnt['retire_decision']} | 0 |
| done, outside the closure | earned guarded completions and decisions; preserved, no action | {cnt['done_outside']} | {done('done_outside')} |
| **total** | | **{len(ix)}** | |

The model grew from {delta['counts']['items_before']} to {delta['counts']['items_after']} items: {', '.join(i['id'] for i in delta['items_added'])}.
Open work on the critical path: **{len(open_a)} items** ({', '.join(f"{v} {k}" for k, v in sorted(by.items(), key=lambda kv: (-kv[1], kv[0])))}), plus the {cnt['a_close']}-item close chain.
Source: `CLOSURE_v2_1.json` (`closure_count` {closure['closure_count']}, `outside_count` {closure['outside_count']}) joined to the live status named above; new items show the status the tracker source computes for them from the same events.

Per acceptance (members overlap): (i) {closure['acceptances']['i']['closure_count']} · (ii) {closure['acceptances']['ii']['closure_count']} · (iii) {closure['acceptances']['iii']['closure_count']}.

## 2. The plan's deferral candidates, examined

| candidate | in the closure? | conclusion |
|---|---|---|""")
    for i in ["J-7", "J-7b", "D-T2", "L0-K"]:
        users = ", ".join(x["id"] for x in model["items"] if i in x["depends_on"]) or "no item"
        w(f"| {i} | {'yes' if cls[i] == 'a' else 'no — consumed only by ' + users} | "
          f"{'critical path' if cls[i] == 'a' else 'deferred (b): ' + decl['deferred'][i]['reason']} |")
    w("""
## 3. Skips can never satisfy an acceptance

The closure lists, per acceptance, every place where an item that accepts skipped inputs could absorb one.
If any of these inputs ends `not_applicable`, the acceptance above it is reported with that gap and the
campaign closes `CLOSED-PARTIAL`.

| acceptance | absorbing item ← skippable input (reason) |
|---|---|""")
    for a, v in closure["acceptances"].items():
        w(f"| ({a}) | " + "; ".join(f"{g['absorbed_by']} ← {g['input']} ({', '.join(g['reasons'])})"
                                      for g in v["gap_candidates"]) + " |")
    w("""
Roots that can themselves end `not_applicable` (the acceptance is then NOT MET, never silently met):
""" + "; ".join(f"({a}) {r}: {', '.join(rs)}" for a, v in closure["acceptances"].items()
                 for r, rs in v["skip_capable_roots"].items()) + """.

## 4. Outside the closure — each item's disposition

| item | live status | class | reason | re-entry / decision |
|---|---|---|---|---|""")
    for i, k in cls.items():
        t = ix[i]["triage"]
        if k == "b":
            w(f"| {i} | {status(i)} | (b) | {t['reason']} | re-entry: {t['re_entry']} |")
    for i, k in cls.items():
        t = ix[i]["triage"]
        if k == "c":
            w(f"| {i} | {status(i)} | (c) | {t['reason']} | {t['basis']} |")
    for i, k in cls.items():
        if k == "retired":
            d = next(x for x in decl["retire_decisions"] if x["retires"] == i)
            w(f"| {i} | {status(i)} | retired | {d['record']['default'].split(' — ', 1)[1]} | `{d['id']}` registered; "
              f"`requires_outcome` approved; `refused` staged for B-2 |")
    for i, k in cls.items():
        if k == "retire_decision":
            w(f"| {i} | {status(i)} | retire-decision | decision item for {ix[i]['triage']['retires']} | staged outcome: refused |")
    for i, k in cls.items():
        if k == "a_close":
            w(f"| {i} | {status(i)} | (a·close) | acceptance (iv); regenerated from the retained set | — |")
    for i, k in cls.items():
        if k == "done_outside":
            w(f"| {i} | {status(i)} | done·outside | earned; evidence preserved | — |")
    cm = delta["close_membership"]
    w(f"""
The close join `JOIN-ALL` now waits for the {cm['after']} retained items (was {cm['before']}): added
{', '.join(cm['added']) or '—'}; removed {', '.join(cm['removed']) or '—'}. The deferred items are not members and are listed
by the close report with their re-entry conditions.

Staged, not published (`STAGED_MODEL_ACTIONS_v2_2.json`; B-2 publishes): the two refusals and the park notes of the
deferred items. Simulated in memory against the captured events, publication would change exactly these items:
{'; '.join(f"{i}: {v['status'][0]} → {v['status'][1]}" for i, v in delta['staged_effects_if_published'].items() if v['status'][0] != v['status'][1])}.

## 5. Schema prerequisites (`KV3-SCHEMA-<n>`)

Admitted schema receipt: `{schema['schema_receipt_id']}` — {schema['tables_count']} tables; ledger of {schema['ledger']['applied_count']} applied migrations
(highest {schema['ledger']['highest_number']}); {len(schema['repository']['migrations_not_in_ledger'])} repository migrations are newer than the receipt and are listed in it.
A missing required column is never a reason to defer its consumer (plan §0 step 3).

| id | consumer | missing column | evidence | state |
|---|---|---|---|---|""")
    for sp in decl["schema_prerequisites"]:
        cols = schema["tables"].get(sp["table"])
        w(f"| {sp['id']} | {sp['consumer']} | `{sp['table']}`: {sp['missing']} | receipt columns: "
          f"{', '.join(cols) if cols else 'TABLE ABSENT'}; KYD-150 (insufficient_evidence) | registered as a critical-path item; "
          f"{sp['consumer']} depends on it; blocked on the Suvarṇa custodian's column contract |")
    w(f"""
Mechanical scan of the open critical-path briefs for `table.column` references against the receipt:
{schema['brief_scan']['summary']}
Further prerequisites found when packets are written (B-4, plan §8 section 4) are added by a model job under new
`KV3-SCHEMA-<n>` ids and re-reviewed.

## 6. Declaration fields (plan §6)

| completion kind | executable items | reviewer rules |
|---|--:|---|""")
    kinds = collections.defaultdict(list)
    for i in model["items"]:
        if "completion_kind" in i:
            kinds[i["completion_kind"]].append(i)
    for k in ("code", "artifact", "operation", "packet"):
        rules = collections.Counter(i["reviewer_rule"] for i in kinds[k])
        w(f"| {k} | {len(kinds[k])} | " + "; ".join(f"{r} ({n})" for r, n in sorted(rules.items())) + " |")
    steps = sum(len(i.get("step_evidence", {})) for i in model["items"])
    w(f"""
Every executable item also names its producer stream and, for each of its required steps ({steps} in total), the
evidence class the step must cite. No step detector is named yet (0 of {steps}): the item's packet names it, and a
step whose detector is null is never recorded (CLAUDE.md §N.8).

## 7. Every item

`class · id · owner · live status · completion kind · brief citation (first pinned sections) — title`
""")
    for i, k in cls.items():
        x = ix[i]
        w(f"- {label[k]} · **{i}** · {x['owner']} · {status(i)} · {x.get('completion_kind', x.get('done_by', '—'))} · "
          f"{cite(x)} — {x['title'][:90]}")
    return "\n".join(o) + "\n"


# ---------------------------------------------------------------- command line

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("build", "check"):
        p = sub.add_parser(name)
        p.add_argument("--base", required=True)
        p.add_argument("--declarations", required=True)
        p.add_argument("--roots", required=True)
        p.add_argument("--out" if name == "build" else "--model", required=True)
    p = sub.add_parser("capture")
    for a in ("--state", "--base", "--events", "--out"):
        p.add_argument(a, required=True)
    p = sub.add_parser("delta")
    for a in ("--base", "--model", "--declarations", "--staged", "--capture", "--events", "--out"):
        p.add_argument(a, required=True)
    p = sub.add_parser("priority")
    for a in ("--model", "--capture", "--out"):
        p.add_argument(a, required=True)
    p = sub.add_parser("report")
    for a in ("--model", "--declarations", "--closure", "--capture", "--schema", "--delta", "--out"):
        p.add_argument(a, required=True)
    p.add_argument("--status", required=True)
    p.add_argument("--review", required=True)
    a = ap.parse_args(argv)

    if a.cmd in ("build", "check"):
        out = render(build(load(a.base), load(a.declarations), load(a.roots)))
        if a.cmd == "build":
            Path(a.out).write_bytes(out)
            print(f"wrote {a.out}: {len(json.loads(out)['items'])} items, sha256 {sha256_bytes(out)}")
            return 0
        if Path(a.model).read_bytes() != out:
            print(f"FAIL {a.model} is not the build of its base and declarations")
            return 1
        print(f"OK {a.model} sha256 {sha256_bytes(out)}")
        return 0
    if a.cmd == "capture":
        base = load(a.base)
        cap = make_capture(load(a.state), base, a.events)
        bad = replay_mismatches(base, read_events_prefix(a.events, cap), cap)
        if bad:
            print(json.dumps(bad, indent=1, ensure_ascii=False))
            print(f"FAIL the reduced detector map does not replay the captured snapshot for {len(bad)} items")
            return 1
        Path(a.out).write_bytes(render(cap))
        print(f"wrote {a.out}: replay equals the capture for {len(cap['item_states'])} items")
        return 0
    if a.cmd == "delta":
        cap = load(a.capture)
        d = compute_delta(load(a.base), load(a.model), load(a.declarations), load(a.staged), cap,
                          read_events_prefix(a.events, cap))
        Path(a.out).write_bytes(render(d))
        print(f"wrote {a.out}: sha256 {sha256_bytes(render(d))}")
        return 0
    if a.cmd == "priority":
        Path(a.out).write_text("\n".join(priority_lines(load(a.model), load(a.capture))) + "\n", encoding="utf-8")
        print(f"wrote {a.out}")
        return 0
    hashes = {"closure_file": sha256_bytes(Path(a.closure).read_bytes()),
              "declarations_file": sha256_bytes(Path(a.declarations).read_bytes()),
              "delta_file": sha256_bytes(Path(a.delta).read_bytes()), "status": a.status, "review": a.review}
    Path(a.out).write_text(report(load(a.model), load(a.declarations), load(a.closure), load(a.capture),
                                  load(a.schema), load(a.delta), hashes), encoding="utf-8")
    print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
