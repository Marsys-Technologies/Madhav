import json, sys, collections
def rows(p): return [json.loads(l) for l in open(p) if l.strip()]
orig = rows(sys.argv[1]); n = len(orig)
for name, p in (("base", sys.argv[2]), ("head", sys.argv[3])):
    new = rows(p)[n:]
    c = collections.Counter((r["state"], r["criterion"]) for r in new)
    print(name, len(new), "new rows:", dict(c))
head_new = rows(sys.argv[3])[n:]; base_new = rows(sys.argv[2])[n:]
closed = [r for r in head_new if r["state"] == "CLOSED"]
print("\nCLOSED by HEAD:", len(closed))
for r in closed: print(" ", r["gap_id"], "|", r["what"][:230])
bo = {r["gap_id"] for r in base_new if r["state"]=="OPEN"}; ho = {r["gap_id"] for r in head_new if r["state"]=="OPEN"}
print("\nOPEN base==head:", bo == ho, sorted(bo))
json.dump([r["gap_id"] for r in closed], open(sys.argv[4], "w"), indent=0)
