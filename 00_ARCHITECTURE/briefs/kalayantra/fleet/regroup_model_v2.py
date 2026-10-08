#!/usr/bin/env python3
"""KĀLA-YANTRA plan model v2 regrouping (velocity amendment §2).

Reads the current plan_model.json and the event log; writes the regrouped model (preview or in place).
Rules: items with events are never removed; per-file splits that have not started are merged into one unit;
dependants are rewired; K8-K<packet> registration items fold into the packet's last K item as a step;
unclaimed control-plane items are dropped (B-DB-BASELINE kept). Prints a summary and runs the model self-check.
"""
import json, pathlib, sys, collections

MODEL = pathlib.Path(sys.argv[1]); EVENTS = pathlib.Path(sys.argv[2]); OUT = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 else None
m = json.loads(MODEL.read_text()); items = {i["id"]: i for i in m["items"]}
touched = {json.loads(l).get("item") for l in EVENTS.read_text().splitlines() if l.strip()}
touched.discard(None)

def merge_group(new_id, members, title, lane=None, keep_first_branch=False):
    """Merge `members` (ordered) into one item `new_id`; dependants of any member depend on new_id."""
    members = [x for x in members if x in items]
    if not members:
        return
    assert new_id in members or new_id not in items, f"{new_id} would overwrite an existing item that is not a member"
    started = [x for x in members if x in touched]
    if started and not keep_first_branch:
        print(f"  skip {new_id}: members already started: {started}"); return
    first = items[members[0]]
    owns, shared, tests, specs, notes, steps, mig = [], [], [], [], [], [], None
    deps = set()
    for x in members:
        it = items[x]; b = it.get("brief") or {}
        for k, acc in (("owns", owns), ("shared", shared), ("tests", tests), ("spec", specs), ("notes", notes)):
            vals = b.get(k) or []
            if isinstance(vals, str): vals = [vals]
            for v in vals:
                if v not in acc: acc.append(v)
        if b.get("migration"): mig = mig or b["migration"]
        steps.append(x.lower().replace(new_id.lower() + "-", "") if x.lower().startswith(new_id.lower()) else x.lower())
        for d in it.get("depends_on") or []:
            if d not in members: deps.add(d)
    new = {**first, "id": new_id, "title": title, "lane": lane or first.get("lane"), "depends_on": sorted(deps),
           "steps": steps, "join": False, "mandatory": any(items[x].get("mandatory", True) for x in members),
           "detector": {"type": "branch_merged", "ref": f"origin/kalayantra/{new_id.lower()}"},
           "brief": {**(first.get("brief") or {}), "owns": owns, "shared": shared, "tests": tests, "spec": specs,
                     "notes": notes + [f"v2.0 regroup of {', '.join(members)} (velocity amendment §2)"],
                     **({"migration": mig} if mig else {})}}
    new.pop("done_by", None)
    for x in members: del items[x]
    items[new_id] = new
    for it in items.values():
        ds = it.get("depends_on") or []
        if any(d in members for d in ds):
            it["depends_on"] = sorted({new_id if d in members else d for d in ds})
    for k, v in (m.get("coverage") or {}).items():
        if isinstance(v, dict):
            for kk, lst in v.items():
                if isinstance(lst, list) and any(x in members for x in lst):
                    v[kk] = sorted({new_id if x in members else x for x in lst})
    print(f"  {new_id} ← {members}")

print("regrouping:")
merge_group("K0a-3", ["K0a-3a", "K0a-3b", "K0a-3c", "K0a-3"], "Layer manifest: candidate and publication tables, open_candidate, candidate_generation, completeness attestation, publication side", keep_first_branch=True)
merge_group("K7-1a", ["K7-1a-common", "K7-1a-now", "K7-1a-ahead", "K7-1a-priority", "K7-1a-elect", "K7-1a-story", "K7-1a-ritual", "K7-1a-explain", "K7-1a-register", "K7-1a"], "Seven retrieval-registry view composites, their shared response contract and registration")
merge_group("KA-1e", ["KA-1-ephemeris", "KA-1-events", "KA-1-geometry", "KA-1-contacts", "KA-1-coverage", "KA-1-api"], "Gochara engine: ephemeris, events, geometry, contacts, coverage, api")
merge_group("KA-1w", ["KA-1-facade", "KA-1-writer", "KA-1"], "Gochara facade and writer")
# the old join K4-2a goes first into K4-2aw so the new core may reuse the id K4-2a without being swallowed
merge_group("K4-2aw", ["K4-2a-writer", "K4-2a-qualify", "K4-2a"], "Convergence writer and qualification")
merge_group("K4-2a", ["K4-2a-schema", "K4-2a-algebra", "K4-2a-jaimini", "K4-2a-groups", "K4-2a-agreement", "K4-2a-contests"], "Convergence core: schema, algebra, Jaimini, groups, agreement, contests")
merge_group("K6-123", ["K6-1", "K6-2", "K6-3"], "Kalasutra, kala_darshana and jivana_parva writers (three additive migrations, one PR)")
merge_group("K9-23", ["K9-2", "K9-3"], "Publication tooling and the layer_verify/publish/rollback executor scripts")

# K8-K<packet> → a declared step on the packet's last K item
fold = {"K8-K0a": "K0a-4", "K8-K12": "K2-2", "K8-K3": "K3-2", "K8-K4": "K4-3", "K8-K5": "K5-G1b", "K8-K6": "K6-5", "K8-K7": "K7-4", "K8-KA": "KA-4b"}
for k8, target in fold.items():
    if k8 in items and target in items and k8 not in touched:
        t = items[target]; t.setdefault("steps", []).append("certification_mapping")
        b = t.setdefault("brief", {})
        notes = b.get("notes") or []; notes = [notes] if isinstance(notes, str) else list(notes)
        notes.append(f"carries {k8}: {items[k8]['title']}"); b["notes"] = notes
        owns = b.get("owns") or []; owns = [owns] if isinstance(owns, str) else list(owns)
        b["owns"] = owns + [o for o in ((items[k8].get("brief") or {}).get("owns") or []) if o not in owns]
        del items[k8]
        for it in items.values():
            ds = it.get("depends_on") or []
            if k8 in ds: it["depends_on"] = sorted({target if d == k8 else d for d in ds})
        print(f"  {k8} folded into {target} as step certification_mapping")

# unclaimed control-plane items are dropped (the control plane is finished); B-DB-BASELINE stays
dropped = []
for iid in list(items):
    if iid.startswith("B-") and iid not in touched and iid != "B-DB-BASELINE" and not items[iid].get("join"):
        dropped.append(iid); del items[iid]
for it in items.values():
    it["depends_on"] = [d for d in (it.get("depends_on") or []) if d in items]
print(f"  dropped unclaimed control items: {dropped}")

# lanes the fleet actually runs (amendment §1): builders k1..k8 (ceiling 12), verifiers v1..v4
for st in m.get("streams", []):
    if st.get("id") == "K":
        st["lanes"] = [f"k{i}" for i in range(1, 13)]; st["worktrees"] = [f"/Users/Dev/kalayantra/wt/k{i}" for i in range(1, 13)]
    if st.get("id") == "V":
        st["lanes"] = [f"v{i}" for i in range(1, 5)]; st["worktrees"] = [f"/Users/Dev/kalayantra/wt/v{i}" for i in range(1, 5)]
cp = m.setdefault("control_plane", {}); cp.setdefault("claims", {})["lease_s"] = 10800   # 3-hour work units (amendment §3)
m["items"] = list(items.values()); m["model_version"] = str(m.get("model_version", "")) + "+v2.0-regroup"
# self-checks
ids = {i["id"] for i in m["items"]}
bad = [(i["id"], d) for i in m["items"] for d in i.get("depends_on", []) if d not in ids]
assert not bad, f"unknown dependencies: {bad}"
def cyc():
    color = {}
    def visit(n, stack):
        if color.get(n) == 1: raise AssertionError("cycle at " + "→".join(stack + [n]))
        if color.get(n) == 2: return
        color[n] = 1
        for d in items[n].get("depends_on", []): visit(d, stack + [n])
        color[n] = 2
    for n in items: visit(n, [])
cyc()
nodet = [i["id"] for i in m["items"] if not i.get("detector") and not i.get("join") and not i["id"].startswith("D-")]
print(f"items: {len(ids)} (was {len(json.loads(MODEL.read_text())['items'])}); no-detector non-join: {nodet}")
if OUT:
    OUT.write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n"); print("written", OUT)
