"""Shared fixtures for the E6.3 tests: a throw-away git repository holding the ledgers `elevated_assets` reads.

Nothing here touches the real repository or a database. `World` builds the five committed inputs (certificate
ledger, E5.5 invalidations + watermark, gap ledger, dispositions, and a MINI asset_census.py whose registry is small
enough to enumerate by hand), commits them, and lets a test change one thing at a time. The record field names are
the ones documented at the top of the E6.3 section of asset_elevation_tracker.py (E5.1's arch 12.16 schema).

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
CERTS, GAPS, INVAL, DISP = (f"{CTRL}/asset_certs.jsonl", f"{CTRL}/asset_gaps.jsonl",
                            f"{CTRL}/asset_cert_invalidations.jsonl", f"{CTRL}/asset_dispositions.jsonl")
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
    "Ldgr.src":  dict(gate="Ldgr",  check="src",  detector="census", layers=ALL_LAYERS, columns_any=None, revision=1),
    "Idem.pat":  dict(gate="Idem",  check="pat",  detector="census", layers=ALL_LAYERS, columns_any=None, revision=2),
    "Idem.alt":  dict(gate="Idem",  check="alt",  detector="census", layers=ALL_LAYERS, columns_any=None, revision=1),
    "Null.x":    dict(gate="Null",  check="x",    detector="census", layers=ALL_LAYERS, columns_any=("c",), revision=1),
    "Build.any": dict(gate="Build", check="any",  detector="census", layers=ALL_LAYERS, columns_any=None, revision=1),
    "Build.reg": dict(gate="Build", check="reg",  detector="census", layers=("L1", "L2"), columns_any=None, revision=1),
    "Reach.f":   dict(gate="Reach", check="f",    detector="census", layers=ALL_LAYERS, columns_any=None, revision=1),
    "Cost.base": dict(gate="Cost",  check="base", detector="census", layers=ALL_LAYERS, columns_any=None, revision=1),
}
NA_RULE_DECISIONS: dict[str, str] = {"Null.x#columns_any": "N-22a"}
REGISTRY_REVISION = 3
'''

FP = hashlib.sha256(b"rows").hexdigest()
RUN_ID = "2026-10-02T10:00:00+05:30"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def writer_path(asset: str) -> str:
    return f"{WRITER_DIR}/{asset}.py"


def writer_body(asset: str, version: int = 1) -> bytes:
    return f"# writer of {asset}, v{version}\n".encode()


def cert(asset, crit, verdict="PASS", *, kind="gate", gen=1, upstream=(), na=None, detector="census", fp=FP,
         layer=None, revision=None, writer=True, **over):
    """One certificate record in E5.1's shape. `revision` defaults to the MINI registry's."""
    layer = layer or {"bg": "L0", "ga": "L1", "bo": "L2", "ka": "L3", "ph": "L4", "mi": "L5"}[asset[:2]]
    mini_rev = {"Ldgr.src": 1, "Idem.pat": 2, "Idem.alt": 1, "Null.x": 1, "Build.reg": 1}.get(crit, 1)
    gate = crit.split(".")[0] if kind == "gate" else None
    key = f"{asset}|{kind}|{crit}"
    rec = dict(asset=asset, layer=layer, kind=kind, gate=gate, criterion=crit,
               criterion_version=(revision or mini_rev) if kind == "gate" else 1,
               registry_revision=3 if kind == "gate" else None, registry_fingerprint="f" * 64 if kind == "gate" else None,
               detector=detector, verdict=verdict, basis=None, na=na,
               evidence=dict(census_run_id=RUN_ID), job_image_tag=None,
               writer_hashes={writer_path(asset): sha(writer_body(asset))} if writer else {},
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
           cert(asset, "Null.x", "N/A", na=dict(NA_NULL), **kw), cert(asset, "Build.any", **kw)]
    if layer_has_build:
        out.append(cert(asset, "Build.reg", **kw))
    return out


def schema_row(doc="schema"):
    return {"asset": "_schema", "_doc": doc}


def jsonl(rows, schema=True) -> str:
    rows = ([schema_row()] if schema else []) + list(rows)
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)


def nonblank_lines(text: str):
    return [ln.rstrip("\r") for ln in text.split("\n") if ln.strip()]


def watermark_for(certs_text: str, **over):
    lines = nonblank_lines(certs_text)
    row = dict(record_type="watermark", certs_lines=len(lines),
               certs_sha256=sha("".join(ln + "\n" for ln in lines).encode()), commit="a" * 40, event_offset=7)
    row.update(over)
    return row


def inval(cert_id, kind="semantic_fingerprint"):
    return dict(record_type="invalidation", cert_id=cert_id, invalidated_by=dict(kind=kind, detail="rows changed"))


def disp(asset, disposition="keep", reason="", additions=()):
    return dict(asset=asset, disposition=disposition, reason=reason, additions=list(additions))


def gap(asset, crit, state="OPEN", kind="gap", gap_id=None, **over):
    row = dict(asset=asset, gap_id=gap_id or f"{asset}-{crit}", kind=kind, criterion=crit, what="w", change="c",
               detector="d", owner="o", gate="g", state=state, ts="2026-10-01T00:00:00+05:30")
    row.update(over)
    return row


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
    """A repo plus the lists that become its committed inputs. `commit()` renders and commits them."""

    def __init__(self, tmp_path, *, census=MINI_CENSUS):
        self.repo = pathlib.Path(tmp_path) / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "main")
        self.census = census
        self.certs, self.gaps, self.disps, self.invals = [], [], [], []
        self.writer_versions = {}
        self.raw = {}            # path -> exact text, replaces the rendered one (malformed-input tests)
        self.watermark = "auto"  # "auto" | dict | None (no watermark row)
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
        recs = [c for c in self.certs if c["asset"] == asset and c["criterion"] == crit and c["kind"] == kind
                and (gen is None or c["generation"] == gen)]
        assert recs, (asset, crit)
        return recs[-1]

    def drop(self, asset, crit, kind="gate"):
        self.certs = [c for c in self.certs if not (c["asset"] == asset and c["criterion"] == crit and c["kind"] == kind)]

    # -- rendering ---------------------------------------------------------------------------------------------
    def render(self):
        certs_text = jsonl(self.certs)
        wm = watermark_for(certs_text) if self.watermark == "auto" else self.watermark
        inv_rows = list(self.invals) + ([wm] if wm is not None else [])
        files = {CERTS: certs_text, GAPS: jsonl(self.gaps), INVAL: jsonl(inv_rows), DISP: jsonl(self.disps),
                 CENSUS: self.census}
        files.update(self.raw)
        return files

    def commit(self, msg="ledgers"):
        files = self.render()
        assets = {c["asset"] for c in self.certs} | {d["asset"] for d in self.disps}
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
