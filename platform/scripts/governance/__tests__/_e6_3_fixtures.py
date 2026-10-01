"""Shared fixtures for the E6.3 tests: a throw-away git repository holding the ledgers `elevated_assets` reads.

Nothing here touches the real repository or a database. `World` builds the committed inputs (certificate
ledger with E5.5 lines, gap ledger, dispositions, a MINI asset_census.py whose registry is small enough to enumerate
by hand, and a MINI registry seed), commits them, and lets a test change one thing at a time. The record field names are
the ones documented at the top of the E6.3 section of asset_elevation_tracker.py (E5.1's arch 12.16 schema).

The certificate ledger is E5.1's hash-chained one (seq, prev_sha256) and carries E5.5's invalidation and watermark
lines inside it; `World` chains and renders it, so a test changes one thing and re-renders.

The tracker module under test is `E6_3_TRACKER_UNDER_TEST` when set (the mutation harness points it at a mutated
copy), else the committed 00_ARCHITECTURE/control/asset_elevation_tracker.py.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[4]
TRACKER_PATH = pathlib.Path(os.environ.get("E6_3_TRACKER_UNDER_TEST")
                            or REPO / "00_ARCHITECTURE/control/asset_elevation_tracker.py")
CTRL = "00_ARCHITECTURE/control"
CERTS, GAPS, DISP = f"{CTRL}/asset_certs.jsonl", f"{CTRL}/asset_gaps.jsonl", f"{CTRL}/asset_dispositions.jsonl"
SEED = "platform/scripts/seed/asset_registry_seed.ts"
GENERATOR = "00_ARCHITECTURE/control/generate_level_map.py"      # the registry-seed parser is read from the ref
LEVEL_MAP = f"{CTRL}/LEVEL_MAP.json"
CENSUS = "platform/scripts/governance/asset_census.py"
WRITER_DIR = "platform/python-sidecar/pipeline/orchestrator/writers"


def load_tracker():
    name = "asset_elevation_tracker_e6_3"
    spec = importlib.util.spec_from_file_location(name, TRACKER_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


MINI_CENSUS = '''\
ALL_LAYERS = ("L0", "L1", "L2", "L3", "L4", "L5")
LAYERS = {
    "L0": dict(prefix="bg_", name="Brahmagyan", scoring="fidelity"),
    "L1": dict(prefix="ga_", name="Ganita", scoring="contribution"),
    "L2": dict(prefix="bo_", name="Bodha", scoring="contribution"),
    "L3": dict(prefix="ka_", name="Kala", scoring="contribution"),
    "L4": dict(prefix="ph_", name="Phala", scoring="contribution"),
    "L5": dict(prefix="mi_", name="Mimamsa", scoring="contribution"),
}
CELL_GATES = ("Ldgr", "Idem", "Null", "Build")
CRITERION_REGISTRY: dict[str, dict] = {
    "Ldgr.src":  dict(gate="Ldgr",  check="src",  detector="census", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),
    "Idem.pat":  dict(gate="Idem",  check="pat",  detector="census", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=2),
    "Idem.alt":  dict(gate="Idem",  check="alt",  detector="census", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),
    "Null.x":    dict(gate="Null",  check="x",    detector="census", layers=ALL_LAYERS, columns_any=("c",), asset_kinds=None, revision=1),
    "Build.any": dict(gate="Build", check="any",  detector="census", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),
    "Build.target": dict(gate="Build", check="target", detector="census", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),
    "Build.reg": dict(gate="Build", check="reg",  detector="census", layers=("L1", "L2"), columns_any=None, asset_kinds=None, revision=1),
    "Reach.f":   dict(gate="Reach", check="f",    detector="census", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),
    "Cost.base": dict(gate="Cost",  check="base", detector="census", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),
}
NA_RULE_DECISIONS: dict[str, str] = {"Null.x#columns_any": "N-22a"}
REGISTRY_REVISION = 3
PASS, PARTIAL = "PASS", "PARTIAL"


def _check_contribution(crit, layer, meas, facts):
    v = meas["v"]
    if v == PASS and (crit.startswith("Null.") or crit == "Narr.fidelity_test"):
        return dict(criterion=crit, v=PARTIAL, state="MEASURED", reason="capped")
    return dict(criterion=crit, v=v)
'''

FP = hashlib.sha256(b"rows").hexdigest()
RUN_ID = "2026-10-02T10:00:00+05:30"
LAYER_OF = {"bg": "L0", "ga": "L1", "bo": "L2", "ka": "L3", "ph": "L4", "mi": "L5"}
LAYER_NAME = {"L0": "brahmagyan", "L1": "ganita", "L2": "bodha", "L3": "kala", "L4": "phala", "L5": "mimamsa"}
# the floor the mini registry satisfies in every layer (tests that exercise the real floor patch it back)
MINI_FLOOR = {"Ldgr": 1, "Idem": 2, "Null": 1, "Build": 1}
# the pinned criterion ids the mini registry satisfies in every layer (Build.reg is L1/L2 only, so it is not pinned)
MINI_PINNED = {"Ldgr": ("Ldgr.src",), "Idem": ("Idem.alt", "Idem.pat"), "Null": ("Null.x",),
               "Build": ("Build.any", "Build.target")}


def mini_patch(monkeypatch, tracker):
    """Pin the floor AND the criterion ids the mini registry satisfies (the real ones name the real registry)."""
    monkeypatch.setattr(tracker, "E63_REQUIRED_FLOOR", MINI_FLOOR)
    monkeypatch.setattr(tracker, "E63_REQUIRED_CRITERIA", MINI_PINNED)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def writer_path(asset: str) -> str:
    return f"{WRITER_DIR}/{asset}.py"


def writer_body(asset: str, version: int = 1) -> bytes:
    return f"# writer of {asset}, v{version}\n".encode()


def cert(asset, crit, verdict="PASS", *, kind="gate", gen=1, upstream=(), na=None, detector="census", fp=FP,
         layer=None, revision=None, writer=True, **over):
    """One certificate record in E5.1's shape (seq / prev_sha256 are added when the ledger is rendered)."""
    layer = layer or LAYER_OF[asset[:2]]
    mini_rev = {"Ldgr.src": 1, "Idem.pat": 2, "Idem.alt": 1, "Null.x": 1, "Build.reg": 1, "Build.any": 1, "Build.target": 1}.get(crit, 1)
    gate = crit.split(".")[0] if kind == "gate" else None
    key = f"{asset}|{kind}|{crit}"
    rec = dict(asset=asset, layer=layer, kind=kind, gate=gate, criterion=crit,
               criterion_version=(revision or mini_rev) if kind == "gate" else 1,
               registry_revision=3 if kind == "gate" else None, registry_fingerprint="f" * 64 if kind == "gate" else None,
               detector=detector, verdict=verdict, basis=None, na=na, inconclusive=False, transitive_only=False,
               evidence=dict(census_run_id=RUN_ID), cross_checked=(kind == "gate"), job_image_tag=None,
               writer_hashes={writer_path(asset): sha(writer_body(asset))} if writer else {},
               writer_hashes_verified=bool(writer),
               writer_hashes_reason=None if writer else "asset has no writer file",
               upstream_cert_ids=list(upstream), semantic_fingerprint=fp if verdict in ("PASS", "N/A") else None,
               cert_key=key, generation=gen, cert_id=f"{key}@{gen}", verified_by="census-run",
               verified_on=RUN_ID, record_version=1)
    rec.update(over)
    return rec


NA_NULL = dict(rule_id="Null.x#columns_any", decision_id="N-22a", basis="applicability_facts", cause=None,
               facts={"columns": ["a"]})


def gate_certs(asset, layer_has_build=True, **kw):
    """Every criterion the MINI registry requires of `asset`'s layer, all satisfied (Null.x as a computed N/A)."""
    out = [cert(asset, "Ldgr.src", **kw), cert(asset, "Idem.pat", **kw), cert(asset, "Idem.alt", **kw),
           cert(asset, "Null.x", "N/A", na=dict(NA_NULL), **kw), cert(asset, "Build.any", **kw),
           cert(asset, "Build.target", **kw)]
    if layer_has_build:
        out.append(cert(asset, "Build.reg", **kw))
    return out


def schema_row(doc="schema"):
    return {"asset": "_schema", "_doc": doc}


def jsonl(rows, schema=True) -> str:
    rows = ([schema_row()] if schema else []) + list(rows)
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)


def chained(rows) -> str:
    """The certificate ledger text: `_schema` row, then every row with seq 1..N and prev_sha256 (E5.1's chain: the
    sha256 of the previous line's bytes, the schema row's for the first). A row that already carries seq or
    prev_sha256 keeps it (so a test can forge one)."""
    schema = json.dumps(schema_row(), ensure_ascii=False)
    lines, prev = [schema], sha(schema.encode())
    for i, r in enumerate(rows, 1):
        r = dict(r)
        r.setdefault("seq", i)
        r.setdefault("prev_sha256", prev)
        line = json.dumps(r, ensure_ascii=False)
        lines.append(line)
        prev = sha(line.encode())
    return "\n".join(lines) + "\n"


def inval(cert_id, code="semantic_fingerprint", walk=1):
    """E5.5's invalidation event for `cert_id` (shape: nikasha_stale_certs.py docstring, LEDGER LINE SHAPES)."""
    asset = cert_id.split("|", 1)[0]
    return dict(type="invalidation", asset=asset, layer=LAYER_OF[asset[:2]], invalidates=cert_id,
                reason=[dict(code=code, recorded="a", observed="b")], walk=walk, detected_by="nikasha_stale_certs.py",
                detected_on=RUN_ID, record_version=1)


def watermark(rows_before, **over):
    """E5.5's watermark event truthfully covering every record in `rows_before` (the lines before it): covers_seq is the
    seq of the last of them, certs_processed / last_cert_id describe the certificates among them."""
    certs = [r for r in rows_before if r.get("kind") in ("gate", "addition") and "cert_id" in r and "type" not in r]
    row = dict(type="watermark", asset="_ledger", covers_seq=len(rows_before), certs_processed=len(certs),
               last_cert_id=certs[-1]["cert_id"] if certs else None, commit="a" * 40, evaluated_on=RUN_ID,
               record_version=1)
    row.update(over)
    return row


def epoch_reset(layer="L1", decision="N-28"):
    return dict(type="epoch_reset", asset="_ledger", layer=layer, decision=decision, reset_on=RUN_ID, record_version=1)


def disp(asset, disposition="keep", reason="", additions=(), decision_id="N-70", decided_on=RUN_ID):
    """One disposition line (chained when rendered). `decision_id=None` reads `unresolved`."""
    return dict(asset=asset, disposition=disposition, reason=reason, decision_id=decision_id, decided_on=decided_on,
                additions=list(additions))


def gap(asset, crit, state="OPEN", kind="gap", gap_id=None, **over):
    row = dict(asset=asset, gap_id=gap_id or f"{asset}-{crit}", kind=kind, criterion=crit, what="w", change="c",
               detector="d", owner="o", gate="g", state=state, ts="2026-10-01T00:00:00+05:30")
    row.update(over)
    return row


def seed_text(assets: dict) -> str:
    """A MINI registry seed (platform/scripts/seed/asset_registry_seed.ts shape): {asset_id: asset_kind}."""
    ents = "".join(
        f"  {{ asset_id: '{a}', layer: '{LAYER_NAME[LAYER_OF[a[:2]]]}', sort_order: 1, depends_on: [], scope: 'global', "
        f"is_active: true, asset_kind: '{k}' }},\n" for a, k in sorted(assets.items()))
    return "export const ASSETS: AssetDef[] = [\n" + ents + "]\n"


def git(repo, *args, check=True):
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
               GIT_COMMITTER_EMAIL="t@t", GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_SYSTEM="/dev/null")
    for k in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        env.pop(k, None)
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {args}: {r.stderr}")
    return r.stdout.strip()


class World:
    """A repo plus the lists that become its committed inputs. `commit()` renders and commits them.

    certs / invals / tail_certs are the certificate-ledger rows, rendered in that order with the watermark between
    `invals` and `tail_certs` (so `tail_certs` are certificates the watermark does NOT cover). `watermark`: "auto"
    (a truthful one), a dict of field overrides, or None (no watermark line)."""

    def __init__(self, tmp_path, *, census=MINI_CENSUS):
        self.repo = pathlib.Path(tmp_path) / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "main")
        self.census = census
        self.certs, self.invals, self.tail_certs, self.gaps, self.disps = [], [], [], [], []
        self.seed_extra = {}
        self.seed_exclude = set()
        self.writer_versions = {}
        self.raw = {}            # path -> exact text/bytes (None deletes the file); replaces the rendered one
        self.watermark = "auto"
        self.level_map = None
        self.last = None

    # -- building blocks --------------------------------------------------------------------------------------
    def asset(self, asset, *, disposition="keep", additions=(), layer_has_build=True):
        self.certs += gate_certs(asset, layer_has_build)
        for a in additions:
            self.certs.append(cert(asset, a, kind="addition"))
        self.disps.append(disp(asset, disposition, additions=additions))
        return self

    def default(self):
        """ga_alpha (L1, fully certified), bg_beta (L0 + one declared addition), ka_gamma (terminal retire)."""
        self.asset("ga_alpha")
        self.asset("bg_beta", additions=["D-GROUNDING"], layer_has_build=False)
        self.disps.append(disp("ka_gamma", "retire", reason="superseded by ka_delta"))
        return self

    def find(self, asset, crit, kind="gate", gen=None):
        recs = [c for c in self.certs + self.tail_certs if c["asset"] == asset and c["criterion"] == crit
                and c["kind"] == kind and (gen is None or c["generation"] == gen)]
        assert recs, (asset, crit)
        return recs[-1]

    def drop(self, asset, crit, kind="gate"):
        self.certs = [c for c in self.certs if not (c["asset"] == asset and c["criterion"] == crit and c["kind"] == kind)]

    # -- rendering ---------------------------------------------------------------------------------------------
    def ledger_rows(self):
        rows = list(self.certs) + list(self.invals)
        if self.watermark is not None:
            over = {} if self.watermark == "auto" else dict(self.watermark)
            rows.append(watermark(rows, **over))
        return rows + list(self.tail_certs)

    def certs_text(self):
        return chained(self.ledger_rows())

    def seed_assets(self):
        assets = {c["asset"] for c in self.certs + self.tail_certs} | {d["asset"] for d in self.disps}
        out = {a: "data" for a in assets if a[:2] in LAYER_OF and a not in self.seed_exclude}
        out.update(self.seed_extra)
        return out

    def render(self):
        files = {CERTS: self.certs_text(), GAPS: jsonl(self.gaps), DISP: chained(self.disps), CENSUS: self.census,
                 SEED: seed_text(self.seed_assets()), GENERATOR: (REPO / GENERATOR).read_text(encoding="utf-8")}
        if self.level_map is not None:
            files[LEVEL_MAP] = self.level_map
        files.update(self.raw)
        return files

    def commit(self, msg="ledgers"):
        files = self.render()
        assets = {c["asset"] for c in self.certs + self.tail_certs} | {d["asset"] for d in self.disps}
        for a in sorted(assets):
            p = self.repo / writer_path(a)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(writer_body(a, self.writer_versions.get(a, 1)))
        for rel, content in files.items():
            p = self.repo / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            if content is None:
                p.unlink(missing_ok=True)
            elif isinstance(content, bytes):
                p.write_bytes(content)
            else:
                p.write_text(content, encoding="utf-8")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "--allow-empty", "-m", msg)
        self.last = git(self.repo, "rev-parse", "HEAD")
        return self.last

    def elevated(self, tracker, ref=None):
        return tracker.elevated_assets(ref or self.last, str(self.repo))


def clone(world_certs):
    return copy.deepcopy(world_certs)
