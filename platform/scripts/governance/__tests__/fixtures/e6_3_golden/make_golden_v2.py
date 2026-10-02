"""Generate the E6.3 golden v2 ledger (N-74 citation_state) with the REAL E5.1 citation-state writer
(nikasha_certify.write_certification, branch suvarna/engine-E5.1-citation-state, record_version 2) and the REAL E5.5
invalidate()/watermark, over the E6.3 mini registry. The writer's CITATION_CRITERIA is patched to the mini registry's
Ldgr.src / Idem.alt (the mini registry has no Carr.D1 / Ldgr.source_presence); the E6.3 tests patch the reader the same way.
Assets: ga_alpha sourced; ga_beta Ldgr sourced_ocr_unverified; ga_gamma Ldgr PASS with a NULL state (caveat true, still counts);
ga_delta Idem.alt NO_DETECTOR / unsourced (the census caps it; not elevated).
"""
import json, os, shutil, subprocess, sys, tempfile, pathlib, importlib.util, hashlib, datetime as dt

OUT = pathlib.Path(sys.argv[1])
E51 = pathlib.Path("/Users/Dev/suvarna-engine-lane-e5-1b/platform/scripts/governance")
E55 = pathlib.Path("/Users/Dev/suvarna-engine-lane-e5-5/platform/scripts/governance")
LANE = pathlib.Path("/Users/Dev/suvarna-engine-lane-e6-3")
combo = pathlib.Path(tempfile.mkdtemp())
for src, name in ((E51, "nikasha_certify.py"), (E51, "asset_census.py"), (E55, "nikasha_stale_certs.py")):
    shutil.copy(src / name, combo / name)
sys.path.insert(0, str(combo))
sys.path.insert(0, str(LANE / "platform/scripts/governance/__tests__"))
from _e6_3_fixtures import MINI_CENSUS, DECL_TEXT, DECLARATIONS  # noqa
import asset_census as ac, nikasha_certify as nc, nikasha_stale_certs as sc  # noqa

ns = {}
exec(MINI_CENSUS, ns)
ac.CRITERION_REGISTRY = ns["CRITERION_REGISTRY"]; ac.CELL_GATES = ns["CELL_GATES"]; ac.NA_RULE_DECISIONS = ns["NA_RULE_DECISIONS"]

repo = pathlib.Path(tempfile.mkdtemp()) / "repo"
repo.mkdir()
def git(*a, date=None):
    e = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t",
             GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_SYSTEM="/dev/null")
    if date: e.update(GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
    return subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True, env=e).stdout.decode()
git("init", "-q", "-b", "main")
WD = "platform/python-sidecar/pipeline/orchestrator/writers"
ASSETS = ["ga_alpha", "ga_beta", "ga_gamma", "ga_delta"]
def wbody(a, v=1): return f"# writer of {a}, v{v}\n".encode()
for a in ASSETS:
    p = repo / WD / f"{a}.py"; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(wbody(a))
(repo / DECLARATIONS).parent.mkdir(parents=True, exist_ok=True); (repo / DECLARATIONS).write_text(DECL_TEXT)   # gates bind to its sha256
(repo / "00_ARCHITECTURE/control/census").mkdir(parents=True); (repo / "00_ARCHITECTURE/control/census/.gitkeep").write_text("")
git("add", "-A"); git("commit", "-q", "-m", "writers", date="2026-09-30T10:00:00+05:30")
ac.ROOT = repo; ac.SIDECAR = repo / "platform/python-sidecar"; ac.WRITERS = repo / WD
ac.CTRL = repo / "00_ARCHITECTURE/control"

RUN = "2026-10-01T10:00:00+05:30"
FP = {a: hashlib.sha256(f"{a} rows".encode()).hexdigest() for a in ASSETS}
nc.CITATION_CRITERIA = ("Ldgr.src", "Idem.alt")
STATE = {("ga_alpha", "Ldgr.src"): "sourced", ("ga_alpha", "Idem.alt"): "sourced",
         ("ga_beta", "Ldgr.src"): "sourced_ocr_unverified", ("ga_beta", "Idem.alt"): "sourced",
         ("ga_gamma", "Ldgr.src"): None, ("ga_gamma", "Idem.alt"): "sourced",
         ("ga_delta", "Ldgr.src"): "sourced", ("ga_delta", "Idem.alt"): "unsourced"}
TOOL = "a" * 40
def census_file(asset):
    cells = {c: dict(v="PASS", measured="m") for c in ("Ldgr.src", "Idem.pat", "Idem.alt", "Build.any", "Build.target", "Build.reg")}
    for crit in ("Ldgr.src", "Idem.alt"):
        st = STATE[(asset, crit)]
        if st is not None:
            cells[crit]["citation_state"] = st
        if st == "unsourced":
            cells[crit]["v"] = "NO_DETECTOR"            # the census caps an unsourced cell at NO_DETECTOR
    rec = dict(asset_id=asset, layer="L1", has_writer=True, writer_files=[f"{asset}.py"], asset_kind="data",
               target_columns=["a"], measurements=cells)
    c = dict(generated=RUN, layer="L1", registry_revision=ac.REGISTRY_REVISION, registry_fingerprint=ac.registry_fingerprint(),
             tool_commit=TOOL, assets=[rec], declarations_sha256=hashlib.sha256(DECL_TEXT.encode()).hexdigest(), declarations_version="1.0.0")
    p = repo / "00_ARCHITECTURE/control/census" / f"census_{asset}.json"
    p.write_text(json.dumps(c)); git("add", "--", str(p)); return p

ledger = repo / "00_ARCHITECTURE/control/asset_certs.jsonl"
def certify(asset, crit, upstream=(), **kw):
    r = nc.write_certification(ledger_path=ledger, init=not ledger.exists(), asset=asset, layer="L1", criterion=crit,
        evidence=dict(census_run_id=RUN, measured="m"), verified_by="census-run", census_path=census_file(asset),
        writer_files=[f"{WD}/{asset}.py"], writer_repo=repo, semantic_fingerprint=FP[asset], upstream_cert_ids=list(upstream),
        verified_on=RUN, **kw)
    return r.cert_id
for a in ASSETS:
    ids = {}
    ids["L"] = certify(a, "Ldgr.src")
    ids["P"] = certify(a, "Idem.pat")
    ids["A"] = certify(a, "Idem.alt", upstream=[ids["L"]])
    certify(a, "Null.x", verdict="N/A", na_rule_id="Null.x#columns_any")
    certify(a, "Build.any"); certify(a, "Build.target"); certify(a, "Build.reg")

observed = {a: dict(writer_hashes={f"{WD}/{a}.py": hashlib.sha256(wbody(a)).hexdigest()}, writer_paths=[f"{WD}/{a}.py"],
                    semantic_fingerprint=FP[a]) for a in ASSETS}

OUT.mkdir(parents=True, exist_ok=True)
sc.invalidate(ledger, observed, commit="b" * 40, now=RUN)
shutil.copy(ledger, OUT / "ledger_v2.jsonl")
print("ok", OUT)
