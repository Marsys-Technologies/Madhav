#!/usr/bin/env python3
"""Real-PG test of DRAFT_NEEDS_NUMBER_l0_transit_engine_citation_curation.sql on a DISPOSABLE local server (unix socket, caller starts/stops by PID).
  run_pg_test_draft_engine_curation.py <socket_dir> <port>
P0 replica fidelity | P1 hash probe -> pin + draft | P2 apply once (only engine.classical_citation x9 + 2 registry rows) | P3 idempotent
P4 guard refusals | P5 reseal necessary | P6 pin mutation | P7 seed parity (engine) | P8 composes with a simulated #3049 rules reseal, either order"""
import hashlib, importlib.util, json, pathlib, re, shutil, subprocess, sys, tempfile
HERE = pathlib.Path(__file__).resolve().parent; CUR = HERE.parent
sys.path.insert(0, str(HERE))
import build_transit_curation as B
PSQL = "/opt/homebrew/bin/psql"; sock, port = sys.argv[1], sys.argv[2]; LOG = []
def log(m): print(m); LOG.append(m)
def psql(db, sql, check=True, file=None):
    cmd = [PSQL, "-X", "-q", "-At", "-h", sock, "-p", port, "-U", "cur", "-d", db, "-v", "ON_ERROR_STOP=1"] + (["-f", file] if file else ["-c", sql])
    p = subprocess.run(cmd, capture_output=True, text=True)
    if check and p.returncode: raise RuntimeError(p.stderr)
    return p
def fresh(db):
    psql("postgres", f"DROP DATABASE IF EXISTS {db}"); psql("postgres", f"CREATE DATABASE {db}")
    subprocess.run([str(HERE / "pg_replica_load.py"), sock, port, db], check=True)
def state(db):
    return json.loads(psql(db, "select json_build_object('rules',(select json_agg(t order by id) from bg_transit_rules t),'engine',(select json_agg(t order by id) from bg_transit_engine t),'moorti',(select json_agg(t order by nakshatra_offset) from bg_transit_moorti t),'registry',(select json_agg(t order by asset_id) from asset_registry t))").stdout)
def checks(db):
    o = {}
    for a in ("bg_transit_engine", "bg_transit_rules"):
        o[a] = psql(db, psql(db, f"select integrity_check_sql from asset_registry where asset_id='{a}'").stdout).stdout.strip()
    return o
def diff(a, b):
    k = {"rules": "id", "engine": "id", "moorti": "nakshatra_offset", "registry": "asset_id"}; d = []
    for t, key in k.items():
        assert len(a[t]) == len(b[t])
        for ra, rb in zip(a[t], b[t]):
            d += [(t, ra[key], c) for c in ra if ra[c] != rb[c]]
    return d
ehash = lambda db: psql(db, B.ENGINE_HASH_SQL).stdout.strip()

fresh("e0"); assert checks("e0") == {"bg_transit_engine": "t", "bg_transit_rules": "t"} and ehash("e0") == B.OLD_ENGINE_HASH
log(f"P0 PASS replica fidelity: both stored contracts read t; engine content hash == pinned pre-state ({B.OLD_ENGINE_HASH[:12]}..)")
_, eng_sql = B.update_statements()
p = psql("e0", f"BEGIN;\n{eng_sql};\nSELECT 'E|'||({B.ENGINE_HASH_SQL});\nROLLBACK;")
pin = re.search(r"E\|([0-9a-f]{64})", p.stdout).group(1); assert pin != B.OLD_ENGINE_HASH and ehash("e0") == B.OLD_ENGINE_HASH
json.dump({"engine": pin}, open(HERE / "engine_pin.json", "w"))
draft = CUR / "drafts" / "DRAFT_NEEDS_NUMBER_l0_transit_engine_citation_curation.sql"
draft.write_text(B.build_engine_sql(pin), encoding="utf8")
log(f"P1 PASS hash probe (rolled back): post-state engine {pin[:12]}.. -> draft regenerated")

fresh("e1"); before = state("e1"); psql("e1", None, file=str(draft)); after = state("e1"); d = diff(before, after)
assert sorted({(t, c) for t, k, c in d}) == [("engine", "classical_citation"), ("registry", "english_description"), ("registry", "integrity_check_sql")], d
assert sum(1 for t, k, c in d if t == "engine") == 9 and sorted({k for t, k, c in d if t == "registry"}) == ["bg_transit_engine", "bg_transit_rules"]
assert not [x for x in d if x[0] in ("rules", "moorti")]
assert checks("e1") == {"bg_transit_engine": "t", "bg_transit_rules": "t"}
assert all(rb[c] == ra[c] for rb, ra in zip(before['engine'], after['engine']) for c in ('graha','avg_daily_motion_deg','zodiac_period_days','sign_residence_days'))
log("P2 PASS apply once: changed = 9 engine.classical_citation + registry (integrity_check_sql, english_description) of the two assets; rules/moorti tables untouched; numeric engine columns identical; both stored contracts read t")
p = psql("e1", None, file=str(draft)); assert "already applied" in p.stderr and diff(after, state("e1")) == []
log("P3 PASS idempotent: re-apply = NOTICE no-op, nothing changed")

muts = {"engine citation altered": "UPDATE bg_transit_engine SET classical_citation = classical_citation||' ' WHERE graha='sun'",
        "engine value altered": "UPDATE bg_transit_engine SET sign_residence_days = 31 WHERE graha='sun'",
        "engine registry lost the engine literal": f"UPDATE asset_registry SET integrity_check_sql = replace(integrity_check_sql,'{B.OLD_ENGINE_HASH}','x') WHERE asset_id='bg_transit_engine'",
        "rules registry lost the engine literal": f"UPDATE asset_registry SET integrity_check_sql = replace(integrity_check_sql,'{B.OLD_ENGINE_HASH}','x') WHERE asset_id='bg_transit_rules'",
        "description drifted": "UPDATE asset_registry SET english_description = english_description||' ' WHERE asset_id='bg_transit_engine'"}
for i, (n, m) in enumerate(muts.items()):
    db = f"e4_{i}"; fresh(db); psql(db, m); pre = state(db); pr = psql(db, None, check=False, file=str(draft))
    assert pr.returncode != 0 and "curation refuses" in pr.stderr, (n, pr.stderr[-300:]); assert diff(pre, state(db)) == []
    log(f"P4 PASS guard refuses on '{n}', nothing changed"); psql("postgres", f"DROP DATABASE {db}")
fresh("e5"); psql("e5", eng_sql + ";"); c = checks("e5"); assert c == {"bg_transit_engine": "f", "bg_transit_rules": "f"}, c
log("P5 PASS reseal necessary: the citation UPDATEs alone turn both stored contracts to f")
fresh("e6"); mf = pathlib.Path(tempfile.mkdtemp()) / "m.sql"
txt = draft.read_text(encoding="utf8"); mut = txt.replace("PARTIALLY SOURCED \u2014 only", "PARTIALLY  SOURCED \u2014 only", 1); assert mut != txt; mf.write_text(mut, encoding="utf8")
pre = state("e6"); pr = psql("e6", None, check=False, file=str(mf)); assert pr.returncode != 0 and "post-flight" in pr.stderr and diff(pre, state("e6")) == []
log("P6 PASS mutation: one altered character of a new citation is caught by the pinned post-state hash, nothing applied")

# P7 seed parity (engine only)
repo = CUR.parents[5]
def load(path, name):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
orig = load(repo / "platform/python-sidecar/brahmagyan/l0_transit.py", "l0o")
pp = B.seed_patch(repo, str(CUR / "drafts" / "DRAFT_l0_transit_engine_seed_curation.patch")); pat = load(pp, "l0p"); shutil.rmtree(pathlib.Path(pp).parent, ignore_errors=True)
live = {r["graha"]: r for r in before["engine"]}; post = {r["graha"]: r for r in after["engine"]}
cols = ("avg_daily_motion_deg", "zodiac_period_days", "sign_residence_days", "classical_citation")
for r in orig.BG_TRANSIT_ENGINE: assert all(r[c] == live[r["graha"]][c] for c in cols)
for r in pat.BG_TRANSIT_ENGINE: assert all(r[c] == post[r["graha"]][c] for c in cols)
assert orig.BG_TRANSIT_RULES == pat.BG_TRANSIT_RULES
log("P7 PASS seed parity: unpatched BG_TRANSIT_ENGINE == live pre-state; patched == post-curation table (9 rows x 4 cols); BG_TRANSIT_RULES byte-identical (#3049's territory untouched)")

# P8 composition with a simulated #3049 rules reseal (rules citations changed, rules sha in the rules check replaced) in both orders
def sim3049(db):
    psql(db, "UPDATE bg_transit_rules SET classical_citation = 'Phaladipika SIM3049' WHERE id = 5")
    newh = psql(db, B.RULES_HASH_SQL).stdout.strip()
    psql(db, f"UPDATE asset_registry SET integrity_check_sql = replace(integrity_check_sql,'{B.OLD_RULES_HASH}','{newh}') WHERE asset_id='bg_transit_rules'")
for order in ("3049-then-engine", "engine-then-3049"):
    db = "e8" + order[0]; fresh(db)
    if order.startswith("3049"): sim3049(db); psql(db, None, file=str(draft))
    else: psql(db, None, file=str(draft)); sim3049(db)
    assert checks(db) == {"bg_transit_engine": "t", "bg_transit_rules": "t"}, (order, checks(db)); psql("postgres", f"DROP DATABASE {db}")
log("P8 PASS composes with a simulated #3049 rules reseal in either order: both stored contracts read t afterwards")
for db in ("e0", "e1", "e5", "e6"): psql("postgres", f"DROP DATABASE IF EXISTS {db}")
(CUR / "drafts" / "PG_TEST_EVIDENCE_transit_engine.txt").write_text("Real-PostgreSQL test of DRAFT_NEEDS_NUMBER_l0_transit_engine_citation_curation.sql (disposable local PG 15, unix socket); tools/run_pg_test_draft_engine_curation.py\n\n" + "\n".join(LOG) + "\n", encoding="utf8")
print("ALL PASS")
