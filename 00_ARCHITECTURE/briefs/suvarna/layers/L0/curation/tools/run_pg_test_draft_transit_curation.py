#!/usr/bin/env python3
"""Real-PostgreSQL test of DRAFT_NEEDS_NUMBER_l0_transit_citation_curation.sql on a DISPOSABLE local
server (unix socket, started/stopped by the caller by recorded PID).  Never touches production.

  run_pg_test_draft_transit_curation.py <socket_dir> <port>

Phases
  P0  replica fidelity: the pre-curation stored integrity checks read true on the loaded snapshot
  P1  hash probe: apply the UPDATE statements in a rolled-back transaction, read the post-state
      content hashes -> pins.json; (re)generate the draft SQL with the pins
  P2  apply once: exactly 32 cells (23 rules + 9 engine citations) + 2 registry rows change,
      nothing else; stored contracts read true; counts stay 76/9
  P3  re-apply: NOTICE no-op, nothing changes (idempotency)
  P4  old-value guards: each of 5 single mutations of the pre-state makes the draft REFUSE with no
      change at all (atomic)
  P5  necessity of the reseal: the UPDATEs alone make the stored rules/engine contracts read false
  P6  mutation proof of the pins: a draft whose one new citation is altered fails its post-flight
  P7  seed parity: the patched l0_transit.py module equals the post-state tables (69 writer-owned
      rules + 9 engine rows) and the unpatched module equals the pre-state
"""
import importlib.util, json, pathlib, subprocess, sys, re, tempfile, shutil

HERE = pathlib.Path(__file__).resolve().parent
CUR = HERE.parent
sys.path.insert(0, str(HERE))
import build_transit_curation as B  # noqa: E402

PSQL = "/opt/homebrew/bin/psql"
sock, port = sys.argv[1], sys.argv[2]
LOG = []


def log(msg):
    print(msg)
    LOG.append(msg)


def psql(db, sql, check=True, file=None, single=False):
    cmd = [PSQL, "-X", "-q", "-At", "-h", sock, "-p", port, "-U", "cur", "-d", db, "-v", "ON_ERROR_STOP=1"] + (["-1"] if single else [])
    cmd += ["-f", file] if file else ["-c", sql]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if check and p.returncode:
        raise RuntimeError(p.stderr)
    return p


def fresh(db):
    psql("postgres", f"DROP DATABASE IF EXISTS {db}")
    psql("postgres", f"CREATE DATABASE {db}")
    subprocess.run([str(HERE / "pg_replica_load.py"), sock, port, db], check=True)


def state(db):
    q = ("select json_build_object("
         "'rules',(select json_agg(t order by id) from bg_transit_rules t),"
         "'engine',(select json_agg(t order by id) from bg_transit_engine t),"
         "'moorti',(select json_agg(t order by nakshatra_offset) from bg_transit_moorti t),"
         "'registry',(select json_agg(t order by asset_id) from asset_registry t))")
    return json.loads(psql(db, q).stdout)


def stored_checks(db):
    out = {}
    for a in ("bg_transit_engine", "bg_transit_rules"):
        sql = psql(db, f"select integrity_check_sql from asset_registry where asset_id='{a}'").stdout
        out[a] = psql(db, sql).stdout.strip()
    return out


def hashes(db):
    e = psql(db, B.ENGINE_HASH_SQL).stdout.strip()
    r = psql(db, B.RULES_HASH_SQL).stdout.strip()
    return e, r


def diff_state(a, b):
    """list of (table, key, column) that differ"""
    d = []
    keys = {"rules": ("id",), "engine": ("id",), "moorti": ("nakshatra_offset",), "registry": ("asset_id",)}
    for t, ks in keys.items():
        for ra, rb in zip(a[t], b[t]):
            for c in ra:
                if ra[c] != rb[c]:
                    d.append((t, ra[ks[0]], c))
        assert len(a[t]) == len(b[t])
    return d


# --------------------------------------------------------------------------------------------
fresh("t0")
sc = stored_checks("t0")
assert sc == {"bg_transit_engine": "t", "bg_transit_rules": "t"}, sc
e0, r0 = hashes("t0")
assert (e0, r0) == (B.OLD_ENGINE_HASH, B.OLD_RULES_HASH), (e0, r0)
log("P0 PASS replica fidelity: stored engine+rules contracts read t; engine/rules content hashes equal the pinned pre-state "
    f"({e0[:12]}.., {r0[:12]}..)")

# P1 -----------------------------------------------------------------------------------------
rules_sql, engine_sql = B.update_statements()
probe = f"BEGIN;\n{rules_sql};\n{engine_sql};\n"
p = psql("t0", probe + "SELECT 'E|'||(" + B.ENGINE_HASH_SQL + ") || '|R|' || (" + B.RULES_HASH_SQL + ");\nROLLBACK;")
m = re.search(r"E\|([0-9a-f]{64})\|R\|([0-9a-f]{64})", p.stdout)
pins = {"engine": m.group(1), "rules": m.group(2)}
assert pins["engine"] != B.OLD_ENGINE_HASH and pins["rules"] != B.OLD_RULES_HASH
assert hashes("t0") == (B.OLD_ENGINE_HASH, B.OLD_RULES_HASH)      # the probe rolled back
json.dump(pins, open(HERE / "pins.json", "w"), indent=1)
draft = CUR / "drafts" / "DRAFT_NEEDS_NUMBER_l0_transit_citation_curation.sql"
draft.write_text(B.build_sql(pins), encoding="utf8")
log(f"P1 PASS hash probe (rolled back): post-state engine {pins['engine'][:12]}.. rules {pins['rules'][:12]}.. -> draft SQL regenerated with pins")

# P2 -----------------------------------------------------------------------------------------
fresh("t1")
before = state("t1")
psql("t1", None, file=str(draft))
after = state("t1")
d = diff_state(before, after)
cols = sorted({(t, c) for t, k, c in d})
assert cols == [("engine", "classical_citation"), ("registry", "english_description"), ("registry", "integrity_check_sql"), ("rules", "classical_citation")], cols
n_rules = sum(1 for t, k, c in d if t == "rules")
n_eng = sum(1 for t, k, c in d if t == "engine")
n_reg = sorted({k for t, k, c in d if t == "registry"})
assert (n_rules, n_eng) == (23, 9) and n_reg == ["bg_transit_engine", "bg_transit_rules"], (n_rules, n_eng, n_reg)
changed_ids = sorted(k for t, k, c in d if t == "rules")
assert changed_ids == sorted([r[0] for r in [(x["id"],) for x in B.S.FACT_ROWS + B.S.INFERENCE_ROWS]]), changed_ids
assert stored_checks("t1") == {"bg_transit_engine": "t", "bg_transit_rules": "t"}
assert (len(after["rules"]), len(after["engine"]), len(after["moorti"])) == (76, 9, 27)
cnt = psql("t1", "select count(*) filter (where classical_citation like 'BPHS Ch.29%'), count(*) filter (where classical_citation like 'Phaladeepika Ch.26 (Gochara Vedha%'), "
                 "count(*) filter (where vedha_house is not null and classical_citation like 'Phaladipika Adh. XXVI, Sloka _ %') from bg_transit_rules").stdout.strip()
assert cnt == "1|0|36", cnt
log("P2 PASS apply once: changed cells = 23 rules.classical_citation + 9 engine.classical_citation + 2 registry rows "
    "(integrity_check_sql, english_description); no other column of any table differs; stored contracts read t; counts 76/9/27; "
    "BPHS Ch.29 remains on 1 row; chapter-only Phaladeepika Ch.26 on 0; the 36 vedha-pair rows untouched")

# P3 -----------------------------------------------------------------------------------------
p = psql("t1", None, file=str(draft))
assert "already applied" in p.stderr, p.stderr
assert diff_state(after, state("t1")) == []
log("P3 PASS idempotent: second apply raised NOTICE 'already applied: no-op' and changed nothing")

# P4 -----------------------------------------------------------------------------------------
mutations = {
    "old citation of id 5 altered": "UPDATE bg_transit_rules SET classical_citation = classical_citation || ' ' WHERE id = 5",
    "phala of id 190 altered": "UPDATE bg_transit_rules SET phala = phala || '.' WHERE id = 190",
    "engine value altered": "UPDATE bg_transit_engine SET sign_residence_days = 31 WHERE graha = 'sun'",
    "registry contract drifted": "UPDATE asset_registry SET integrity_check_sql = integrity_check_sql || ' ' WHERE asset_id = 'bg_transit_rules'",
    "registry description drifted": "UPDATE asset_registry SET english_description = english_description || ' ' WHERE asset_id = 'bg_transit_engine'",
}
for i, (name, mut) in enumerate(mutations.items()):
    db = f"t4_{i}"
    fresh(db)
    psql(db, mut)
    pre = state(db)
    p = psql(db, None, check=False, file=str(draft))
    assert p.returncode != 0 and "curation refuses" in p.stderr, (name, p.stderr[-400:])
    assert diff_state(pre, state(db)) == [], name
    msg = next(l for l in p.stderr.splitlines() if "curation refuses" in l)
    log(f"P4 PASS guard refuses on '{name}' and changed nothing ({msg.split('ERROR:')[-1].strip()[:120]})")

# P4b: the row-level old-citation guard, exercised on its own (table-hash guard disabled in a test copy)
fresh("t4b")
psql("t4b", "UPDATE bg_transit_rules SET classical_citation = classical_citation || ' ' WHERE id = 5")
weak = draft.read_text(encoding="utf8").replace("IF h_engine IS DISTINCT FROM c_engine_old OR h_rules IS DISTINCT FROM c_rules_old THEN", "IF false THEN", 1)
assert weak != draft.read_text(encoding="utf8")
wf = pathlib.Path(tempfile.mkdtemp()) / "weak.sql"
wf.write_text(weak, encoding="utf8")
pre = state("t4b")
p = psql("t4b", None, check=False, file=str(wf))
assert p.returncode != 0 and "expected 23 bg_transit_rules rows, updated 22" in p.stderr, p.stderr[-300:]
assert diff_state(pre, state("t4b")) == []
log("P4b PASS row-level guard on its own: with the table-hash guard disabled, a row whose old citation differs makes the UPDATE match 22 not 23 -> raises 'expected 23 ... updated 22', nothing applied")

# P5 -----------------------------------------------------------------------------------------
fresh("t5")
psql("t5", rules_sql + ";\n" + engine_sql + ";")
assert stored_checks("t5") == {"bg_transit_engine": "f", "bg_transit_rules": "f"}
log("P5 PASS the reseal is necessary: the citation UPDATEs alone make both stored integrity contracts read f")

# P6 -----------------------------------------------------------------------------------------
fresh("t6")
mutant = draft.read_text(encoding="utf8").replace("Sloka 22 — phaladeepika:PG330:C1", "Sloka 23 — phaladeepika:PG330:C1", 1)
assert mutant != draft.read_text(encoding="utf8")
mf = pathlib.Path(tempfile.mkdtemp()) / "mutant.sql"
mf.write_text(mutant, encoding="utf8")
pre = state("t6")
p = psql("t6", None, check=False, file=str(mf))
assert p.returncode != 0 and "post-flight: content hash mismatch" in p.stderr, p.stderr[-300:]
assert diff_state(pre, state("t6")) == []
log("P6 PASS mutation: one altered sloka number in the draft is caught by the pinned post-state hash (post-flight raises, nothing applied)")

# P7 -----------------------------------------------------------------------------------------
repo = CUR.parents[5]


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


orig = load_module(repo / "platform/python-sidecar/brahmagyan/l0_transit.py", "l0_orig")
patched_path = B.seed_patch(repo, str(CUR / "drafts" / "DRAFT_l0_transit_seed_curation.patch"))
patched = load_module(patched_path, "l0_patched")
shutil.rmtree(pathlib.Path(patched_path).parent, ignore_errors=True)
live_rules = {(r["graha"], r["rule_type"], r["primary_house"]): r for r in B.RULES}
post = {(r["graha"], r["rule_type"], r["primary_house"]): r for r in after["rules"]}
post_eng = {r["graha"]: r for r in after["engine"]}
live_eng = {r["graha"]: r for r in B.ENGINE}
cmpcols = ("vedha_house", "phala", "classical_citation", "rule_notes")
assert len(orig.BG_TRANSIT_RULES) == 69
for r in orig.BG_TRANSIT_RULES:
    k = (r["graha"], r["rule_type"], r["primary_house"])
    for c in cmpcols:
        assert r.get(c) == live_rules[k][c], ("orig!=live", k, c)
for r in patched.BG_TRANSIT_RULES:
    k = (r["graha"], r["rule_type"], r["primary_house"])
    for c in cmpcols:
        assert r.get(c) == post[k][c], ("patched!=post", k, c)
for r in orig.BG_TRANSIT_ENGINE:
    le = live_eng[r["graha"]]
    for c in ("avg_daily_motion_deg", "zodiac_period_days", "sign_residence_days", "classical_citation"):
        assert r[c] == le[c], ("orig engine!=live", r["graha"], c)
for r in patched.BG_TRANSIT_ENGINE:
    pe = post_eng[r["graha"]]
    for c in ("avg_daily_motion_deg", "zodiac_period_days", "sign_residence_days", "classical_citation"):
        assert r[c] == pe[c], ("patched engine!=post", r["graha"], c)
log("P7 PASS seed parity: UNPATCHED l0_transit.py == live pre-state (69 writer-owned rules x 4 columns, 9 engine rows x 4 columns); "
    "PATCHED module == post-curation tables; the 7 migration-owned double-transit rows are outside the module by design")

# P8 -----------------------------------------------------------------------------------------
# attribution_state interplay with migration 1268 / PR #3044 (column + token-exact backfill applied FIRST)
ADD_COL = ("ALTER TABLE bg_transit_rules ADD COLUMN attribution_state text CHECK (attribution_state IN ('sourced','unsourced','refuted'));"
           "UPDATE bg_transit_rules SET attribution_state='refuted' WHERE classical_citation LIKE 'BPHS Ch.29 (Gochara Phala%';"
           "UPDATE bg_transit_rules SET attribution_state='unsourced' WHERE classical_citation LIKE 'UNSOURCED %';")
fresh("t8")
psql("t8", ADD_COL)
pre8 = psql("t8", "select count(*) filter (where attribution_state='refuted'), count(*) filter (where attribution_state='unsourced'), count(*) filter (where attribution_state is null) from bg_transit_rules").stdout.strip()
assert pre8 == "19|6|51", pre8
p = psql("t8", None, file=str(draft), single=True)
assert "18 FACT rows set to sourced" in p.stderr and "3 INFERENCE rows reset from refuted to NULL" in p.stderr, p.stderr
post8 = psql("t8", "select attribution_state, count(*) from bg_transit_rules group by 1 order by 1 nulls last").stdout.split()
st = dict(x.split("|") for x in post8)
assert st.get("refuted") == "1" and st.get("sourced") == "18" and st.get("unsourced") == "6" and sum(int(v) for v in st.values()) == 76, st
ids_sourced = psql("t8", "select string_agg(id::text, ',' order by id) from bg_transit_rules where attribution_state='sourced'").stdout.strip()
assert ids_sourced == ",".join(str(i) for i in sorted(r["id"] for r in B.S.FACT_ROWS)), ids_sourced
assert psql("t8", "select attribution_state from bg_transit_rules where id=199").stdout.strip() == "refuted"
assert psql("t8", "select count(*) from bg_transit_rules where id in (200,201,202,203,204) and attribution_state is null").stdout.strip() == "5"
assert stored_checks("t8") == {"bg_transit_engine": "t", "bg_transit_rules": "t"}
p = psql("t8", None, file=str(draft), single=True)       # idempotent
assert "already applied" in p.stderr
log("P8 PASS attribution_state with 1268 applied first (19 refuted + 6 unsourced): after the draft the 18 FACT rows are 'sourced', the 5 Ketu INFERENCE rows are NULL (3 reset from refuted, 2 were already NULL), "
    "Ketu 12th stays 'refuted', the 6 UNSOURCED rows stay 'unsourced'; stored contracts still read t; re-apply is a no-op. Without the column the block NOTICEs and skips (P2).")
fresh("t8b")
psql("t8b", ADD_COL)
psql("t8b", "UPDATE bg_transit_rules SET attribution_state='unsourced' WHERE id=5")
pre = state("t8b")
pr = psql("t8b", None, check=False, file=str(draft), single=True)
assert pr.returncode != 0 and "attribution_state other than" in pr.stderr, pr.stderr[-300:]
assert diff_state(pre, state("t8b")) == []
log("P8b PASS a re-sourced row in an unexpected attribution_state ('unsourced') makes the whole file refuse (single transaction: nothing applied)")

for db in ["t0", "t1", "t4b", "t5", "t6", "t8", "t8b"] + [f"t4_{i}" for i in range(len(mutations))]:
    psql("postgres", f"DROP DATABASE IF EXISTS {db}")
(CUR / "drafts" / "PG_TEST_EVIDENCE.txt").write_text(
    "Real-PostgreSQL test of DRAFT_NEEDS_NUMBER_l0_transit_citation_curation.sql (disposable local PG 15, unix socket)\n"
    "run by tools/run_pg_test_draft_transit_curation.py\n\n" + "\n".join(LOG) + "\n", encoding="utf8")
print("ALL PASS")
