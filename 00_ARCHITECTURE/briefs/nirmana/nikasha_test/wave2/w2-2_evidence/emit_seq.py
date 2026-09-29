"""emit_seq.py WHICH(base|head) CTRLDIR : emit the stored Proof-2 census documents of WHICH onto CTRLDIR,
using WHICH's own emit_gaps (base = the 931dbc479 worktree module, head = this checkout)."""
import os, sys, json
which, ctrl = sys.argv[1], sys.argv[2]
os.environ["NIKASHA_CONTROL_DIR"] = ctrl
S = "/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/e1effe6d-cae4-4643-b098-d49444a83a68/scratchpad/w2-2"
root = f"{S}/wt_base" if which == "base" else "/Users/Dev/madhav-nikasha"
sys.path.insert(0, f"{root}/platform/scripts/governance")
import asset_census as ac
assert str(ac.CTRL) == ctrl, ac.CTRL
for L in "L0 L1 L2 L3 L4 L5".split():
    c = json.load(open(f"{S}/census/{which}_{L}.json"))[L]
    print(which, L, "appended/present/closed/reopened =", ac.emit_gaps(c))
