#!/usr/bin/env python3
"""nikasha_scorecard.py -- Suvarna E1.1: the machine-readable T1-T5 scorecard ("the engine's own test").

WHAT T1-T5 ARE (NIKASHA_CHANGE_REGISTER_v2_0.md section 1; NIKASHA_TEST_CAMPAIGN_PROMPT_v1_0.md Phases 2/3/5; the
2026-09-26 campaign report's freeze grid, branch campaign/nikasha-test):

  T1  finds what is there          plant a known defect for every inspector check; the census must fail THAT check
                                   for THAT asset and no other; a mutated detector must be noticed by the suite
  T2  does not invent what isn't   production census per layer; every verdict cell of a stratified sample re-derived
                                   independently; zero disagreements
  T3  a fix closes a row           a repair closes the ledger row BY MEASUREMENT (never unearned), the tracker moves,
                                   a regression re-opens it
  T4  works on a layer it wasn't   the census runs on L1-L5 in production with no errored cell and every active asset
      built against                measured
  T5  the pieces agree             tiers, L0 instance, pilots, tracker, ledgers, inspector, manifest agree on counts,
                                   names and vocabularies (vocabulary cross-check V1-V17, drift_detector, manifest)

WHAT THIS GENERATOR IS. A read-only, deterministic, OFFLINE recomputation of those tests from (a) saved census JSON,
(b) the ledgers and register and tier documents AT A GIT REF (read only through `git show <ref>:path`, never the working
tree), (c) an optional plant-evidence file for T1. Same inputs => byte-identical output (no timestamps, no absolute
paths). It records its own sha256, the inspector's last commit and blob hash, the ref and the inspector's registry
revision/fingerprint, so a later re-proof (E1.7, `scorecard_pass`, CODE-48) can bind to them.

EARNED SIGNAL (CLAUDE.md N.8). Every verdict below is computed by a detector that can fail; the module's tests plant a
defect for each rule and assert the verdict moves. A cell whose input is missing or stale reads UNMEASURED, and a cell
for which no offline detector exists at all reads NO_DETECTOR: neither is ever a pass (a vocabulary extension of Track E
section 5's PASS|FAIL|PARTIAL, recorded in the scorecard's `vocabulary`). A census is STALE unless every identity it
carries matches the ref: registry fingerprint, a clean inspector whose blob at the census's own `tool_commit` equals the
blob at the ref, and the declarations blob. Its cells then read UNMEASURED and carry the verdict they would give as
`observed_on_stale_input: would_be_<V>` (information, never a verdict). A test that reads FAIL says why in `fail_basis`
(a measured defect, or only a known-defect register row still open).

INPUTS. The repo at --ref is read ONLY through git (a shallow clone is refused: E1.7's CI must use fetch-depth: 0). The
censuses default to those committed under 00_ARCHITECTURE/control/census, read at the ref, so --check needs the repository
alone; --census-dir names an outside directory instead. A census is identified by its layer and sha256, never a file name;
several files for one layer (an appended run) are normal and the newest full census by head stamp wins. The ref's
asset_census.py is EXECUTED (scrubbed environment) to read its registry: do not run this against an untrusted ref.

CLI
  nikasha_scorecard.py --ref REF [--repo DIR] [--census-dir DIR] [--t1-evidence FILE] [--out FILE]
  nikasha_scorecard.py --check [--out FILE] [--ref REF] [--repo DIR] [--census-dir DIR] [--t1-evidence FILE]

  generate: writes --out atomically (default 00_ARCHITECTURE/control/NIKASHA_T1_T5_SCORECARD.json under --repo; an
            existing --out must itself be a scorecard) and prints one line per test. The one and only write.
  --check:  recompute with the committed file's recorded `ref` (unless --ref) and compare bytes.
Exit: 0 generated / identical  2 --check differs (names what)  5 script error (unreadable input, unresolvable ref,
      shallow clone, malformed census or evidence, --out not a scorecard, T1 evidence used but not supplied).
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SCHEMA = "nikasha_scorecard/1"
GEN_REL = "platform/scripts/governance/nikasha_scorecard.py"
INSPECTOR_REL = "platform/scripts/governance/asset_census.py"
OUT_REL = "00_ARCHITECTURE/control/NIKASHA_T1_T5_SCORECARD.json"

P = "00_ARCHITECTURE/"
N = P + "briefs/nirmana/"
REGISTER_REL = N + "NIKASHA_CHANGE_REGISTER_v2_0.md"
GAPS_REL = P + "control/asset_gaps.jsonl"
CERTS_REL = P + "control/asset_certs.jsonl"
T1_DOC = P + "MADHAV_PRODUCT_DEFINITION_FINAL.md"
T2_DOC = N + "MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md"
T3_DOC = N + "LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md"
T4_DOC = N + "ASSET_ELEVATION_TEMPLATE_v2_0.md"
L0_DOC = N + "MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v3_0.md"
PILOT_DIR = N + "l0_assets/"
TRACKER_REL = P + "control/asset_elevation_tracker.py"
MANIFEST_REL = P + "CAPABILITY_MANIFEST.json"
DECL_REL = "platform/scripts/governance/asset_declarations.json"
CENSUS_REPO_DIR = P + "control/census/"   # the censuses committed to the repo: the default census input, read AT THE REF
WRITERS_PREFIX = "platform/python-sidecar/"   # scope of the independent @register scan (non-test .py)

VERDICTS = ("PASS", "FAIL", "PARTIAL", "NO_DETECTOR", "UNMEASURED")
LAYERS = ("L0", "L1", "L2", "L3", "L4", "L5")
T4_LAYERS = ("L1", "L2", "L3", "L4", "L5")
MEASURE_DETECTOR = "asset_census.py:measure()"
CLOSABLE = ("PASS", "N/A")           # mirrors asset_census.CLOSABLE (R57): the only verdicts that close a gap
LIVE_STATES = ("OPEN", "IN_PROGRESS")
LEDGER_STATES = ("OPEN", "IN_PROGRESS", "CLOSED", "WITHDRAWN")
E1_T1_SCHEMA = "nikasha_t1_evidence/1"
HARNESS_REL = "platform/scripts/governance/nikasha_plant.py"   # the T1 plant harness (E1.7 prerequisite, PR #3088)
# The files the harness's own verifier requires `runtime_files_sha256` to name (nikasha_plant.RUNTIME_FILES + DECLARATIONS_REL +
# D1_FIXTURE_REL + GEN_REL). The harness also hashes every repo file its D1 declaration cites: those extras are allowed, any of
# these missing is a problem. Kept as ONE constant here; the tests compare it with the harness's when the harness is importable.
T1_REQUIRED_RUNTIME_FILES = (
    INSPECTOR_REL,
    "platform/scripts/governance/carriage_d1.py",
    "platform/scripts/governance/check_fact_category_pinning.py",
    "platform/scripts/governance/fact_category_pin_allowlist.json",
    "platform/scripts/governance/check_no_raw_token_in_narrative.py",
    "platform/scripts/governance/no_raw_token_narrative_allowlist.json",
    "platform/python-sidecar/pipeline/orchestrator/dag_edge_guard.py",
    "platform/scripts/governance/asset_declarations.json",
    "platform/scripts/governance/__tests__/fixtures/phaladeepika_latta_d1_fixture.json",
    HARNESS_REL,
)
# Why a check cannot be planted (the campaign's own findings, T1_RESULTS.md section 5). A reason outside this closed list
# is not accepted, and an unplantable check never counts as covered: T1 can be at most PARTIAL while one is declared.
UNPLANTABLE_REASONS = (
    "constant_verdict_no_per_asset_input",   # Complete.width, Carr.detector, Reach.fields: nothing per-asset to mutate
    "reported_not_graded",                   # NOT_GENERIC: the check never opens or closes a gap
    "needs_external_service",                # the defect cannot be planted in a disposable database
)

DEFINITIONS = {
    "T1": "finds what is there: a planted defect makes the inspector fail that check for that asset and no other; "
          "a mutated detector is noticed by the suite",
    "T2": "does not invent what isn't: every census verdict of the sampled assets re-derives independently; "
          "zero disagreements per layer",
    "T3": "a fix closes a row: the ledger row closes by measurement, never unearned, the tracker moves, "
          "a regression re-opens it",
    "T4": "works on a layer it wasn't built against: the census runs on L1-L5 in production, no errored cell, "
          "every active asset measured",
    "T5": "the pieces agree: tiers, L0 instance, pilots, tracker, ledgers, inspector and manifest agree on counts, "
          "names and vocabularies",
}

# Register rows bound to each test. T1, T2 and T5 bind by the register's `found by` column (the row was found BY that
# test's run). T3 and T4 are named explicitly, because the source column over-captures (the T3 loop also surfaced a
# data row, R59) or has no row sourced "T4": T3 = the campaign report's "FAIL in production tooling (R57/R58)"; T4 =
# its grid's L3-not-runnable rows R40/R41 plus the register's own "Exercised on L1-L5 (T4)" row R24. Pattern-bound
# rows decide the precondition only when BLOCKS_FREEZE / BLOCKS_LAYER; explicit rows always do. MEASURED (R84) is a
# measurement record, not a closure: it reads partial.
BIND_SOURCE = {
    "T1": r"\bP2 T1\b",
    "T2": r"\bP2 T2\b|\bP2 handverify\b",
    "T3": r"\bP3 T3\b",
    "T5": r"\bP5 T5\b",
}
BIND_EXPLICIT = {"T3": ("R57", "R58"), "T4": ("R24", "R40", "R41")}
EXPLICIT_ONLY = {r for rows in BIND_EXPLICIT.values() for r in rows}
BLOCKING = ("BLOCKS_FREEZE", "BLOCKS_LAYER")
SEVERITIES = BLOCKING + ("DEGRADES", "COSMETIC")
CLOSED_STATES = ("CLOSED", "DONE")
PARTIAL_STATES = ("CLOSED_ON_BRANCH", "PARTIAL", "DEFERRED", "MEASURED")
OPEN_STATES = ("OPEN", "IN_PROGRESS")      # any other state word (e.g. WITHDRAWN) is unknown: UNMEASURED, never a guessed FAIL

ENGINE_CLAIMS_NOT_COVERED = [
    "build run-level states are written truthfully (no census criterion measures run-level state)",
    "last_error is written on a failed asset (no census criterion measures it)",
    "cascade and downstream reporting of a failed dependency (no census criterion measures it)",
]


class ScorecardError(Exception):
    """An input that cannot be read or is malformed. The CLI maps it to exit 5; it never degrades to a verdict."""


# ───────────────────────────── git access (read-only, at a ref) ─────────────────────────────

def _git(repo, *args, check=True):
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    if check and p.returncode != 0:
        raise ScorecardError(f"git {' '.join(args)} failed: {p.stderr.decode('utf-8', 'replace').strip()}")
    return p


def resolve_ref(repo, ref):
    p = _git(repo, "rev-parse", "--verify", "--quiet", "--end-of-options", f"{ref}^{{commit}}", check=False)
    sha = p.stdout.decode().strip()
    if p.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ScorecardError(f"cannot resolve ref {ref!r} in {repo}")
    return sha


def assert_not_shallow(repo):
    """A shallow clone makes `git log -1 -- <file>` return HEAD, silently changing inspector_commit. E1.7's CI checkout
    must be `fetch-depth: 0`."""
    out = _git(repo, "rev-parse", "--is-shallow-repository").stdout.decode().strip()
    if out == "true":
        raise ScorecardError("shallow clone: inspector_commit and census provenance cannot be established "
                             "(use a full clone; in CI set fetch-depth: 0)")


class RepoAt:
    """Reads files of one commit through git only; caches; a missing path reads None."""

    def __init__(self, repo, sha):
        self.repo, self.sha = str(repo), sha
        self._bytes = {}
        self._tree = None

    def _all_paths(self):
        if self._tree is None:
            out = _git(self.repo, "ls-tree", "-r", "--name-only", "-z", self.sha).stdout.decode("utf-8", "replace")
            self._tree = set(p for p in out.split("\0") if p)
        return self._tree

    def exists(self, path):
        return path in self._all_paths()

    def list(self, prefix):
        return sorted(p for p in self._all_paths() if p.startswith(prefix))

    def raw(self, path):
        if path not in self._bytes:
            if path not in self._all_paths():
                self._bytes[path] = None
            else:
                self._bytes[path] = _git(self.repo, "cat-file", "blob", f"{self.sha}:{path}").stdout
        return self._bytes[path]

    def prefetch(self, paths):
        """Read many blobs through ONE `git cat-file --batch` process (the sidecar scan reads hundreds of files)."""
        todo = [p for p in paths if p not in self._bytes and p in self._all_paths()]
        if not todo:
            return
        req = "".join(f"{self.sha}:{p}\n" for p in todo).encode("utf-8")
        p = subprocess.run(["git", "-C", self.repo, "cat-file", "--batch"], input=req, capture_output=True)
        if p.returncode != 0:
            raise ScorecardError("git cat-file --batch failed: " + p.stderr.decode("utf-8", "replace").strip())
        out, pos = p.stdout, 0
        for path in todo:
            nl = out.index(b"\n", pos)
            head = out[pos:nl].split()
            if len(head) != 3 or head[1] != b"blob":
                raise ScorecardError(f"unexpected cat-file answer for {path}: {out[pos:nl]!r}")
            size = int(head[2])
            self._bytes[path] = out[nl + 1:nl + 1 + size]
            pos = nl + 1 + size + 1

    def text(self, path):
        b = self.raw(path)
        return None if b is None else b.decode("utf-8", "replace")

    def sha256(self, path):
        b = self.raw(path)
        return None if b is None else hashlib.sha256(b).hexdigest()

    def blob_sha256_at(self, commit, path):
        """sha256 of `path` as of another commit; None when the commit or the path does not exist in this repository."""
        if not re.fullmatch(r"[0-9a-f]{40}", commit or ""):
            return None
        p = _git(self.repo, "cat-file", "blob", f"{commit}:{path}", check=False)
        return hashlib.sha256(p.stdout).hexdigest() if p.returncode == 0 else None

    def last_commit(self, path):
        out = _git(self.repo, "log", "-1", "--format=%H", self.sha, "--", path).stdout.decode().strip()
        return out or None


# ───────────────────────────── the inspector's registry at the ref ─────────────────────────────

_REGISTRY_SNIPPET = r'''
import json, sys
sys.path.insert(0, ".")
import asset_census as a
print(json.dumps(dict(
    revision=a.REGISTRY_REVISION,
    fingerprint=a.registry_fingerprint(),
    criteria={k: dict(gate=v.get("gate"), detector=v.get("detector"), layers=list(v.get("layers") or ()))
              for k, v in a.CRITERION_REGISTRY.items()},
    cell_gates=list(a.CELL_GATES),
    retired=sorted(a.RETIRED_CRITERIA)), sort_keys=True))
'''


_FACTS_CACHE = {}


def registry_facts(rp):
    """(revision, fingerprint, criteria, cell_gates, retired) of asset_census at the ref, or None when it cannot be
    imported. Runs the ref's inspector module in a throw-away isolated subprocess with a scrubbed environment; reads
    nothing else. It EXECUTES the ref's code: do not point this generator at an untrusted ref."""
    src = rp.raw(INSPECTOR_REL)
    if src is None:
        return None
    key = hashlib.sha256(src).hexdigest()
    if key in _FACTS_CACHE:
        return _FACTS_CACHE[key]
    facts = _registry_facts_uncached(src)
    _FACTS_CACHE[key] = facts
    return facts


def _registry_facts_uncached(src):
    with tempfile.TemporaryDirectory(prefix="nikasha_scorecard_") as d:
        (Path(d) / "asset_census.py").write_bytes(src)
        try:
            # the ref's inspector is executed: scrub the environment (no DATABASE_URL, PG*, tokens) and never run an
            # untrusted PR ref through this generator
            p = subprocess.run([sys.executable, "-I", "-c", _REGISTRY_SNIPPET], cwd=d, capture_output=True, timeout=120,
                               env={"PATH": "/usr/bin:/bin", "PYTHONHASHSEED": "0", "LC_ALL": "C"})
        except (OSError, subprocess.TimeoutExpired):
            return None
    if p.returncode != 0:
        return None
    try:
        facts = json.loads(p.stdout.decode().strip().splitlines()[-1])
    except (ValueError, IndexError):
        return None
    if not isinstance(facts.get("fingerprint"), str) or not isinstance(facts.get("criteria"), dict):
        return None
    return facts


# ───────────────────────────── cells ─────────────────────────────

def mk(kind, verdict, reason=None, **extra):
    assert verdict in VERDICTS, verdict
    c = {"kind": kind, "verdict": verdict}
    if reason is not None:
        c["reason"] = reason
    c.update(extra)
    return c


def combine(cells):
    """The test verdict. Any FAIL => FAIL; every cell PASS => PASS; otherwise PARTIAL when at least one MEASUREMENT cell
    is PASS, else UNMEASURED. A precondition cell can fail a test but can never make it partially measured."""
    vs = [c["verdict"] for c in cells.values()]
    if "FAIL" in vs:
        return "FAIL"
    if vs and all(v == "PASS" for v in vs):
        return "PASS"
    if any(c["kind"] == "measurement" and c["verdict"] == "PASS" for c in cells.values()):
        return "PARTIAL"
    return "UNMEASURED"


# ───────────────────────────── register (precondition cells) ─────────────────────────────

_ROW = re.compile(r"^\| (R\d+) \| (.*?) \| ([^|]*?) \| (" + "|".join(SEVERITIES) + r") \| ([^|]*?) \| ([^|]*?) \| (.*) \|\s*$")


def parse_register(text):
    rows = {}
    for line in text.split("\n"):
        m = _ROW.match(line)
        if not m:
            continue
        rid, _t, source, sev, _d, _e, state = m.groups()
        word = re.match(r"[A-Z_]+", re.sub(r"[*`]", "", state).strip())
        word = word.group(0) if word else "UNKNOWN"
        cls = ("closed" if word in CLOSED_STATES else "partial" if word in PARTIAL_STATES
               else "open" if word in OPEN_STATES else "unknown")
        rows[rid] = dict(source=source.strip(), severity=sev, state=word, cls=cls)
    return rows


def known_defect_cell(test, reg):
    if reg is None:
        return mk("precondition", "UNMEASURED", "register not readable at ref")
    bound, missing = {}, []
    if test in BIND_EXPLICIT:
        for rid in BIND_EXPLICIT[test]:
            if rid in reg:
                bound[rid] = reg[rid]
            else:
                missing.append(rid)
    else:
        pat = re.compile(BIND_SOURCE[test])
        for rid, r in reg.items():
            if rid not in EXPLICIT_ONLY and pat.search(r["source"]):
                bound[rid] = r
    blocking = {rid: r for rid, r in bound.items() if r["severity"] in BLOCKING or test in BIND_EXPLICIT}
    opn = sorted(rid for rid, r in blocking.items() if r["cls"] == "open")
    par = sorted(rid for rid, r in blocking.items() if r["cls"] == "partial")
    unk = sorted(rid for rid, r in blocking.items() if r["cls"] == "unknown")
    nonblocking = sorted(rid for rid, r in bound.items() if rid not in blocking and r["cls"] == "open")
    extra = dict(rows={rid: r["state"] for rid, r in sorted(blocking.items())}, open=opn, partial=par,
                 nonblocking_open=nonblocking, missing_rows=sorted(missing), unknown_state=unk)
    if opn:
        return mk("precondition", "FAIL", f"{len(opn)} blocking register row(s) open", **extra)
    if unk:
        return mk("precondition", "UNMEASURED", "bound row(s) carry a state word the scorecard does not know: "
                  + ", ".join(f"{r}={blocking[r]['state']}" for r in unk), **extra)
    if missing:
        return mk("precondition", "UNMEASURED", "bound register row(s) absent from the register", **extra)
    if not blocking:
        return mk("precondition", "UNMEASURED", "no register row is bound to this test", **extra)
    if par:
        return mk("precondition", "PARTIAL", f"{len(par)} row(s) closed on a branch / partial / deferred", **extra)
    return mk("precondition", "PASS", None, **extra)


# ───────────────────────────── census ─────────────────────────────

_CENSUS_NAME = re.compile(r"census_L[0-5]\.json|asset_census_.*\.json")


def _census_items_from_dir(census_dir):
    d = Path(census_dir)
    if not d.is_dir():
        raise ScorecardError(f"census dir not found: {census_dir}")
    return [(p.name, p.read_bytes()) for p in sorted(d.iterdir()) if p.is_file() and _CENSUS_NAME.fullmatch(p.name)]


def _census_items_from_repo(rp):
    paths = [x for x in rp.list(CENSUS_REPO_DIR) if x.count("/") == CENSUS_REPO_DIR.count("/")
             and _CENSUS_NAME.fullmatch(x.rsplit("/", 1)[-1])]
    rp.prefetch(paths)
    return [(x.rsplit("/", 1)[-1], rp.raw(x)) for x in paths]


def _generated_key(doc):
    import datetime as _dt
    try:
        t = _dt.datetime.fromisoformat(str(doc.get("generated")))
        if t.tzinfo is None:
            t = t.replace(tzinfo=_dt.timezone.utc)
        return t.timestamp()
    except ValueError:
        return float("-inf")


def load_census(items):
    """items: [(file name, bytes)]. One census per layer. Several files for a layer (an appended run) are normal: the
    newest FULL census wins by its head stamp (`generated`); a scoped (partial) census is chosen only when no full one
    exists. Two candidates with the same stamp and different bytes are refused. The file name is NEVER recorded:
    a census is identified by its layer and the sha256 of its bytes, so the same bytes read from the repo or from an
    outside directory give the same scorecard."""
    by_layer = {}
    for name, raw in items:
        try:
            doc = json.loads(raw)
        except ValueError as exc:
            raise ScorecardError(f"census {name} is not JSON: {exc}")
        keys = [k for k in doc if re.fullmatch(r"L[0-5]", k)] if isinstance(doc, dict) else []
        if len(keys) != 1 or not isinstance(doc[keys[0]], dict) or not isinstance(doc[keys[0]].get("assets"), list):
            raise ScorecardError(f"census {name} does not carry exactly one layer document with an assets list")
        ld = doc[keys[0]]
        scoped = isinstance(ld.get("scope"), dict) and bool(ld["scope"].get("partial"))
        by_layer.setdefault(keys[0], []).append(dict(name=name, sha256=hashlib.sha256(raw).hexdigest(), doc=ld, scoped=scoped))
    out = {}
    for layer, cands in sorted(by_layer.items()):
        full = [c for c in cands if not c["scoped"]]
        pool = full or cands
        best = max(_generated_key(c["doc"]) for c in pool)
        top = sorted({c["sha256"] for c in pool if _generated_key(c["doc"]) == best})
        if len(top) > 1:
            raise ScorecardError(f"{layer}: {len(top)} different censuses share the newest head stamp "
                                 f"({', '.join(c['name'] for c in pool if _generated_key(c['doc']) == best)}); cannot pick one")
        pick = next(c for c in pool if c["sha256"] == top[0])
        out[layer] = dict(sha256=pick["sha256"], doc=pick["doc"])
    return out


def freshness(entry, facts, rp):
    """A census is usable for today's tooling only when every identity it carries matches the ref: the registry
    fingerprint, an inspector that is clean and whose blob at the census's own `tool_commit` equals the blob at the ref,
    and the declarations blob. The registry fingerprint never covers detector SQL, which is why the blob is compared."""
    d = entry["doc"]
    if facts is None:
        return False, "registry_unreadable_at_ref"
    if isinstance(d.get("scope"), dict) and d["scope"].get("partial"):
        return False, "scoped_census"
    if d.get("tool_dirty") is not False:
        return False, "tool_dirty"
    if d.get("registry_fingerprint") != facts["fingerprint"]:
        return False, f"stale_census(registry rev {d.get('registry_revision')} != ref rev {facts['revision']})"
    tc = d.get("tool_commit")
    if not isinstance(tc, str) or not re.fullmatch(r"[0-9a-f]{40}", tc) or tc == "0" * 40:
        return False, "stale_census(tool_commit missing)"
    if d.get("declarations_sha256") != rp.sha256(DECL_REL):
        return False, "stale_census(declarations_sha256 differs from the declarations at the ref)"
    at_tool = rp.blob_sha256_at(tc, INSPECTOR_REL)
    if at_tool is None:
        return False, "stale_census(tool_commit not in this repository)"
    if at_tool != rp.sha256(INSPECTOR_REL):
        return False, "stale_census(inspector blob at tool_commit differs from the ref's)"
    return True, ""


def from_census(census, fresh, layers, fn, kind="measurement", **extra):
    """Run `fn({layer: doc})` -> (verdict, reason, extra) over `layers`, gated by census presence and freshness."""
    missing = [lyr for lyr in layers if lyr not in census]
    stale = {lyr: fresh[lyr][1] for lyr in layers if lyr in census and not fresh[lyr][0]}
    if missing:
        return mk(kind, "UNMEASURED", "census missing for " + ",".join(missing), **extra)
    v, reason, more = fn({lyr: census[lyr]["doc"] for lyr in layers})
    if stale:
        why = "; ".join(f"{lyr}: {r}" for lyr, r in sorted(stale.items()))
        return mk(kind, "UNMEASURED", why, observed_on_stale_input=f"would_be_{v}", observed_detail=more, **extra)
    return mk(kind, v, reason, **{**extra, **more})


def census_assets(doc):
    return doc["assets"]


def t4_layer(docs):
    (doc,) = docs.values()
    assets = doc["assets"]
    n, pop = len(assets), doc.get("population_active")
    cells_of = [[m for m in (a.get("measurements") or {}).values() if isinstance(m, dict)] for a in assets]
    errored = sum(1 for cs in cells_of for m in cs if m.get("v") == "ERRORED")
    ids = [a.get("asset_id") for a in assets]
    no_cells = sorted(str(i) for i, cs in zip(ids, cells_of) if not any(m.get("v") not in (None, "ERRORED") for m in cs))
    dup_ids = sorted({str(i) for i in ids if ids.count(i) > 1})
    info = dict(assets_measured=n, population_active=pop, errored_cells=errored, assets_without_a_measured_cell=no_cells,
                duplicate_asset_ids=dup_ids)
    if n == 0:
        return "FAIL", "no asset measured", info
    if not isinstance(pop, int) or pop != n or doc.get("n_assets") != n:
        return "FAIL", f"population: {n} measured vs {pop} active", info
    if dup_ids:
        return "FAIL", f"duplicate asset id(s): {', '.join(dup_ids)}", info
    if no_cells:
        return "FAIL", f"{len(no_cells)} asset(s) carry no measured (non-ERRORED) cell", info
    if errored:
        return "FAIL", f"{errored} ERRORED cell(s)", info
    return "PASS", None, info


SIDECAR_PREFIX = "platform/python-sidecar/"


def _is_test_path(path):
    parts = path.split("/")
    name = parts[-1]
    return any(x in ("tests", "__tests__", "__pycache__") for x in parts) or name.startswith("test_") or name.endswith("_test.py")


def _module_str_constants(tree):
    consts = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    consts[t.id] = node.value.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) \
                and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            consts[node.target.id] = node.value.value
    return consts


def registered_ids_in(source):
    """Asset ids registered by a `@register(<id>)` decorator in one module: a string literal or a module-level string
    constant (the form every L3/L5 writer uses: `@register(ASSET_ID)`). A docstring mention is not a registration."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return None
    consts = _module_str_constants(tree)
    ids = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call) or not dec.args:
                continue
            fn = dec.func
            name = fn.id if isinstance(fn, ast.Name) else fn.attr if isinstance(fn, ast.Attribute) else None
            if name != "register":
                continue
            a = dec.args[0]
            if isinstance(a, ast.Constant) and isinstance(a.value, str):
                ids.append(a.value)
            elif isinstance(a, ast.Name) and a.id in consts:
                ids.append(consts[a.id])
    return ids


def writers_index(rp):
    """asset_id -> files registering it, over every non-test .py under the python sidecar at the ref. Independent of
    the inspector (which follows imports from writers/): a different method over a different, wider scope."""
    idx, unparsable = {}, 0
    paths = [p for p in rp.list(SIDECAR_PREFIX) if p.endswith(".py") and not _is_test_path(p)]
    rp.prefetch(paths)
    for path in paths:
        src = rp.text(path) or ""
        if "register" not in src:
            continue
        ids = registered_ids_in(src)
        if ids is None:
            unparsable += 1
            continue
        for aid in ids:
            idx.setdefault(aid, []).append(path)
    return idx, unparsable


def t2_rederive(rp):
    def fn(docs):
        idx, unparsable = writers_index(rp)
        dis, compared = [], 0
        for layer in sorted(docs):
            for a in docs[layer]["assets"]:
                hw = a.get("has_writer")
                if not isinstance(hw, bool):
                    dis.append(dict(asset=a.get("asset_id"), layer=layer, census="NO_HAS_WRITER", rederived="UNKNOWN"))
                    continue
                hits = idx.get(a["asset_id"], [])
                expected = ("PASS" if hw else "FAIL") if hits else ("FAIL" if hw else "N/A")
                m = (a.get("measurements") or {}).get("Build.registered")
                got = m.get("v") if isinstance(m, dict) else "ABSENT"
                compared += 1
                if got != expected:
                    dis.append(dict(asset=a["asset_id"], layer=layer, census=got, rederived=expected))
        info = dict(assets_compared=compared, disagreements=dis, unparsable_modules=unparsable)
        if compared == 0:
            return "UNMEASURED", "no asset compared", info
        return ("FAIL" if dis else "PASS"), (f"{len(dis)} disagreement(s)" if dis else None), info
    return fn


# ───────────────────────────── ledger ─────────────────────────────

def parse_ledger(text):
    rows = []
    for i, line in enumerate(text.split("\n"), 1):
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except ValueError as exc:
            raise ScorecardError(f"asset_gaps.jsonl line {i} is not JSON: {exc}")
        if not isinstance(r, dict):
            raise ScorecardError(f"asset_gaps.jsonl line {i} is not an object")
        if r.get("asset") == "_schema":
            continue
        rows.append(r)
    return rows


def _is_meas_closure(r):
    return str(r.get("state", "")).upper() == "CLOSED" and str(r.get("what", "")).startswith("CLOSED by measurement")


def ledger_history(rows):
    seqs = {}
    for r in rows:
        if "gap_id" in r:
            seqs.setdefault(r["gap_id"], []).append(r)
    flips, reopens, standing = [], [], []
    for gid, seq in sorted(seqs.items()):
        live, closed_by_meas = False, False
        for r in seq:
            st = str(r.get("state", "OPEN")).upper()
            if st in LIVE_STATES:
                if closed_by_meas and str(r.get("what", "")).startswith("RE-OPENED by measurement"):
                    reopens.append(gid)
                live = True
            elif _is_meas_closure(r) and live:
                flips.append(gid)
                closed_by_meas = True
        last = seq[-1]
        if gid in flips and _is_meas_closure(last):
            standing.append(gid)
    retirements = sorted({r["gap_id"] for r in rows if r.get("closed_by") == "retirement" and "gap_id" in r})
    return dict(seqs=seqs, flips=sorted(set(flips)), reopens=sorted(set(reopens)), standing=sorted(set(standing)),
                retirements=retirements)


def t3_cells(rp, census, fresh):
    text = rp.text(GAPS_REL)
    if text is None:
        miss = mk("measurement", "UNMEASURED", "asset_gaps.jsonl not readable at ref")
        return {"closure_by_measurement": miss, "closures_earned": dict(miss), "regression_reopen": dict(miss),
                "tracker_moves": mk("measurement", "NO_DETECTOR", "see below")}, None
    hist = ledger_history(parse_ledger(text))

    def closure(docs):
        n = len(hist["flips"])
        info = dict(measurement_closures=n, retirement_closures=len(hist["retirements"]))
        if n == 0:
            return "UNMEASURED", "no OPEN->CLOSED-by-measurement transition in the ledger", info
        return "PASS", None, info

    def earned(docs):
        cell_of = {}
        for layer, d in docs.items():
            for a in d["assets"]:
                for crit, m in (a.get("measurements") or {}).items():
                    if isinstance(m, dict):
                        cell_of[(a["asset_id"], crit)] = m.get("v")
        unearned, unjoinable = [], []
        for gid in hist["standing"]:
            last = hist["seqs"][gid][-1]
            v = cell_of.get((last.get("asset"), last.get("criterion")))
            if v is None:
                unjoinable.append(gid)
            elif v not in CLOSABLE:
                unearned.append(gid)
        info = dict(standing_closures=len(hist["standing"]), unearned=unearned, unjoinable=unjoinable)
        if unearned:
            return "FAIL", f"{len(unearned)} closure(s) whose census cell is not PASS or N/A", info
        if unjoinable:
            return "UNMEASURED", f"{len(unjoinable)} closure(s) with no census cell to join", info
        if not hist["standing"]:
            return "UNMEASURED", "no standing measurement closure", info
        return "PASS", None, info

    def regress(docs):
        info = dict(reopened_gap_ids=hist["reopens"])
        if hist["reopens"]:
            return "PASS", None, info
        return "NO_DETECTOR", "no CLOSED -> RE-OPENED by measurement transition in the ledger: a regression must be induced " \
                              "(seeded cycle: test_a2_emit_gaps_closure.py, bound by the E1.7 CI run)", info

    cells = {
        "closure_by_measurement": from_census(census, fresh, LAYERS, closure),
        "closures_earned": from_census(census, fresh, LAYERS, earned),
        "regression_reopen": from_census(census, fresh, LAYERS, regress),
        "tracker_moves": mk("measurement", "NO_DETECTOR",
                            "the tracker needs the live registry (a database); a transition needs two tracker runs around a repair"),
    }
    gaps = len(hist["seqs"])
    return cells, gaps


# ───────────────────────────── T1 evidence ─────────────────────────────

def load_t1_evidence(path):
    if path is None:
        return None
    p = Path(path)
    try:
        raw = p.read_bytes()
        doc = json.loads(raw)
    except (OSError, ValueError) as exc:
        raise ScorecardError(f"T1 evidence unreadable: {exc}")
    if not isinstance(doc, dict) or doc.get("schema") != E1_T1_SCHEMA:
        raise ScorecardError(f"T1 evidence must carry schema {E1_T1_SCHEMA!r}")
    plants = doc.get("plants")
    if not isinstance(plants, list) or not all(isinstance(x, dict) and isinstance(x.get("check"), str)
                                               and isinstance(x.get("detected"), bool) for x in plants):
        raise ScorecardError("T1 evidence `plants` must be a list of objects with a string `check` and a bool `detected`")
    if not isinstance(doc.get("inspector_blob_sha256"), str):
        raise ScorecardError("T1 evidence must record the `inspector_blob_sha256` it ran against")
    if not isinstance(doc.get("unplantable", {}), dict) or not isinstance(doc.get("mutation", {}), dict):
        raise ScorecardError("T1 evidence `unplantable` and `mutation` must be objects")
    h = doc.get("harness_sha256")
    if h is not None and not (isinstance(h, str) and re.fullmatch(r"[0-9a-f]{64}", h)):
        raise ScorecardError("T1 evidence `harness_sha256` must be 64 lowercase hex digits (the sha256 of the harness run record)")
    return dict(sha256=hashlib.sha256(raw).hexdigest(), doc=doc)


def t1_record_sha256(doc):
    """The hash of the evidence record's own fields, as the plant harness defines it (nikasha_plant.run_record_sha256,
    PR #3088): INTEGRITY, not authenticity. Recomputed here, never trusted: a hand-written or edited record fails."""
    rec = dict(
        harness_file_sha256=doc.get("harness_file_sha256"), runtime_files_sha256=doc.get("runtime_files_sha256"),
        inspector_tree_dirty=doc.get("inspector_tree_dirty"), runtime_files_dirty=doc.get("runtime_files_dirty"),
        inspector_blob_sha256=doc["inspector_blob_sha256"], registry=doc["registry"], partial=doc.get("partial", False),
        plants=[{k: r.get(k) for k in ("id", "check", "asset", "planted", "detected", "verdict_before", "verdict_after",
                                        "collateral", "same_asset_effects", "restore_ok", "error")} for r in doc["plants"]],
        unplantable=doc["unplantable"], unplantable_stale=doc["unplantable_stale"],
        uncovered_required=doc["uncovered_required"],
        mutation=dict(suite_notices=doc["mutation"].get("suite_notices"),
                      mutants=[{k: m.get(k) for k in ("id", "check", "plant", "file", "noticed", "mutant_detected",
                                                       "mutant_verdict_after")} for m in doc["mutation"].get("mutants", [])]))
    return hashlib.sha256(json.dumps(rec, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def t1_evidence_problems(doc, rp):
    """Why the plant evidence cannot be read as a measurement of the tree at the ref (empty = consistent). Checks: the older
    evidence shape (no runtime_files_sha256 / dirty flags); the record hash recomputed from the record's own fields;
    every runtime_files_sha256 entry and harness_file_sha256 against the git blob at the ref; the inspector and harness entries
    present and agreeing with inspector_blob_sha256 / harness_file_sha256; a dirty or unknown tree. A record that passes proves
    it matches the tree, not who produced it (the CI job that ran the harness is the authenticity)."""
    files = doc.get("runtime_files_sha256")
    if not isinstance(files, dict) or "inspector_tree_dirty" not in doc or "runtime_files_dirty" not in doc \
            or "harness_file_sha256" not in doc:
        return ["older evidence shape: no runtime_files_sha256 / harness_file_sha256 / dirty flags to compare with the tree at the ref"]
    why = []
    try:
        if t1_record_sha256(doc) != doc.get("harness_sha256"):
            why.append("harness_sha256 does not equal the hash recomputed from the record's own fields")
    except (KeyError, TypeError, AttributeError) as exc:
        return [f"the record is malformed ({type(exc).__name__}: {exc})"]
    if not files or not all(isinstance(k, str) and isinstance(v, str) for k, v in files.items()):
        return why + ["runtime_files_sha256 is empty or malformed"]
    for rel in T1_REQUIRED_RUNTIME_FILES:
        if rel not in files:
            why.append(f"runtime_files_sha256 does not name {rel}")
    if doc.get("partial") is not False:
        why.append("a partial (--only) run is not a T1 record: no coverage or mutation claim can be read from it")
    if doc.get("uncovered_required") != []:
        why.append(f"the harness itself reports uncovered required check(s): {doc.get('uncovered_required')!r}")
    bad_coll = sorted(str(x.get("id", i)) for i, x in enumerate(doc["plants"]) if not isinstance(x.get("collateral"), list))
    if bad_coll:
        why.append(f"plant(s) whose collateral is not a list: {', '.join(bad_coll)}")
    for rel in sorted(files):
        got = rp.sha256(rel)
        if got != files[rel]:
            why.append(f"{rel}: the evidence records {files[rel][:12]}, the ref has {str(got)[:12]}")
    if doc.get("harness_file_sha256") != files.get(HARNESS_REL):
        why.append("harness_file_sha256 does not equal the runtime_files_sha256 entry for the harness")
    if doc.get("inspector_blob_sha256") != files.get(INSPECTOR_REL):
        why.append("inspector_blob_sha256 does not equal the runtime_files_sha256 entry for the inspector")
    if doc.get("inspector_tree_dirty") is not False or doc.get("runtime_files_dirty") != []:
        why.append(f"the evidence was produced from a dirty or unknown tree (inspector_tree_dirty={doc.get('inspector_tree_dirty')!r}, "
                   f"runtime_files_dirty={doc.get('runtime_files_dirty')!r})")
    return why


def _names_check(entry, check):
    """Does a re-test entry name `check`? The check name, then anything that is not a continuation of the name (end, space, tab,
    colon, ...). `Idem.pattern`, `Idem.pattern: stale` and `Idem.pattern<TAB>reads x` all name it; `Idem.patternX` does not."""
    return re.match(re.escape(check) + r"(?![A-Za-z0-9_]|\.[A-Za-z0-9_])", entry.lstrip()) is not None


def declared_unplantable(doc, required):
    """(covered_by_declaration, refused): a required check counts as covered by declaration ONLY when its reason is in the closed
    list AND the harness's own re-test of the claim is in the evidence (`unplantable_stale` is a list of strings) and does not name
    it (the re-test asserts the cell reads only NOT_GENERIC on every asset of every census the run took). A re-test containing a
    non-string entry cannot be read, so it refuses every declaration (fail closed)."""
    claims = doc.get("unplantable", {})
    stale = doc.get("unplantable_stale")
    covered, refused = [], {}
    unreadable = isinstance(stale, list) and not all(isinstance(x, str) for x in stale)
    for c in sorted(claims):
        if c not in required:
            continue
        if claims[c] not in UNPLANTABLE_REASONS:
            refused[c] = "reason outside the closed list"
        elif not isinstance(stale, list):
            refused[c] = "no re-test of the claim in the evidence"
        elif unreadable:
            refused[c] = "the re-test carries a non-string entry: unreadable"
        elif any(_names_check(x, c) for x in stale):
            refused[c] = "the harness's re-test found the claim stale"
        else:
            covered.append(c)
    return covered, refused


def t1_cells(ev, facts, inspector_blob, rp):
    none = "no plant evidence supplied: the plant harness (nikasha_plant.py, PR #3088) is not on main"
    if ev is None:
        return (mk("measurement", "NO_DETECTOR", none), mk("measurement", "NO_DETECTOR", none), None)
    d = ev["doc"]
    plants = d["plants"]
    n = len(plants)

    def both(why):
        return (mk("measurement", "UNMEASURED", why), mk("measurement", "UNMEASURED", why), n)
    if d["inspector_blob_sha256"] != inspector_blob:
        return both(f"stale plant evidence: measured against inspector blob {d['inspector_blob_sha256'][:12]}, "
                    f"ref has {str(inspector_blob)[:12]}")
    if "harness_sha256" not in d or d["harness_sha256"] is None:
        return both("plant evidence is not bound to a harness run: `harness_sha256` is absent")
    problems = t1_evidence_problems(d, rp)
    if problems:
        return both("plant evidence cannot be read as a measurement of the ref: " + "; ".join(problems))
    if n == 0:
        return both("plant evidence carries no plant: nothing was planted, so nothing was detected")
    def pid(i, x):
        return str(x.get("id", i))
    faulty = sorted(pid(i, x) for i, x in enumerate(plants)
                    if x.get("planted", True) is not True or x.get("error") or x.get("harness_error"))
    undetected = sorted(pid(i, x) for i, x in enumerate(plants) if x["detected"] is not True and pid(i, x) not in faulty)
    collateral = sorted(pid(i, x) for i, x in enumerate(plants) if x.get("collateral"))
    unrestored = sorted(pid(i, x) for i, x in enumerate(plants) if x.get("restore_ok") is not True)
    required = []
    if isinstance(facts, dict) and isinstance(facts.get("criteria"), dict):
        required = sorted(c for c, e in facts["criteria"].items()
                          if isinstance(e, dict) and e.get("detector") == MEASURE_DETECTOR)
    if not required:
        why = ("registry not readable at ref: the required check set is unknown" if not isinstance(facts, dict)
               else f"the registry at the ref names no check with detector {MEASURE_DETECTOR}: the required set is empty, "
                    "so coverage cannot be judged (a renamed detector string would otherwise read as full coverage)")
        return both(why)
    covered = {x["check"] for x in plants
               if x.get("planted", True) is True and x["detected"] is True and not x.get("collateral")
               and x.get("restore_ok") is True and not x.get("error") and not x.get("harness_error")}
    decl_ok, decl_refused = declared_unplantable(d, set(required))
    uncovered = [c for c in required if c not in covered and c not in decl_ok]
    extra = dict(plants=n, required_checks=len(required), uncovered=uncovered, undetected=undetected,
                 collateral=collateral, faulty_plants=faulty, declared_unplantable=decl_ok,
                 declared_unplantable_refused=decl_refused, declared_unplantable_count=len(decl_ok))
    if faulty:
        plant = mk("measurement", "FAIL", "plant(s) not planted or carrying an error: the harness itself fails these", **extra)
    elif undetected or collateral:
        plant = mk("measurement", "FAIL", "a planted defect was missed or touched another asset", **extra)
    elif unrestored:
        plant = mk("measurement", "UNMEASURED", "plant(s) not restored: " + ",".join(unrestored), **extra)
    elif uncovered:
        plant = mk("measurement", "PARTIAL", f"{len(uncovered)} registry check(s) with neither a detected plant nor a "
                   "re-tested declaration of unplantability", **extra)
    else:
        plant = mk("measurement", "PASS", None, **extra)
    plant["detail"] = (f"{plant['verdict']}, {len(decl_ok)} declared unplantable" if decl_ok else plant["verdict"])
    mut = d.get("mutation", {}).get("suite_notices")
    mutants = d.get("mutation", {}).get("mutants")
    if mut is True:
        if not isinstance(mutants, list) or not mutants:
            mcell = mk("measurement", "UNMEASURED", "the record claims the suite noticed the mutation but lists no mutant")
        elif any(not isinstance(m, dict) or m.get("noticed") is not True for m in mutants):
            mcell = mk("measurement", "FAIL", "the record claims the suite noticed the mutation but a listed mutant was not noticed")
        else:
            mcell = mk("measurement", "PASS", None, mutants=len(mutants))
    elif mut is False:
        mcell = mk("measurement", "FAIL", "the mutated detector was not noticed by the suite")
    else:
        mcell = mk("measurement", "NO_DETECTOR", "evidence carries no mutation result")
    return plant, mcell, n


# ───────────────────────────── T5 detectors ─────────────────────────────

def split_frontmatter(text):
    """(frontmatter, body). Frontmatter is the leading `---` ... `---` block; its changelog lines are historical and
    legitimately quote the wording a later fix removed from the body."""
    m = re.match(r"---[ \t]*\n(.*?\n)---[ \t]*(?:\n|$)", text, re.S)
    return (m.group(1), text[m.end():]) if m else ("", text)


def _without_changelog(front):
    """Frontmatter minus its `changelog:` block (the lines up to the next top-level key)."""
    out, skipping = [], False
    for ln in front.split("\n"):
        if re.match(r"changelog:", ln):
            skipping = True
            continue
        if skipping and re.match(r"\S", ln):
            skipping = False
        if not skipping:
            out.append(ln)
    return "\n".join(out)


class Docs:
    def __init__(self, rp):
        self.rp = rp

    def text(self, path):
        return self.rp.text(path)

    def body(self, path):
        t = self.rp.text(path)
        return None if t is None else split_frontmatter(t)[1]

    def front(self, path):
        t = self.rp.text(path)
        return None if t is None else split_frontmatter(t)[0]

    def pilots(self):
        return [p for p in self.rp.list(PILOT_DIR) if p.endswith(".md") and "ELEVATION_BRIEF" in p]


def _missing(paths, d):
    return [p for p in paths if d.text(p) is None]


def _um(binds, why):
    return mk("measurement", "UNMEASURED", why, binds=binds)


def _verdict(binds, fail_reason, hits, **extra):
    if hits:
        return mk("measurement", "FAIL", fail_reason, binds=binds, hits=hits, **extra)
    return mk("measurement", "PASS", None, binds=binds, **extra)


def t5_eight_gates(d, facts):
    b = ["V1", "R63", "R77"]
    files = [T4_DOC, L0_DOC, *d.pilots()]
    miss = _missing([T4_DOC, L0_DOC], d)
    if miss:
        return _um(b, "not readable at ref: " + ",".join(miss))
    # the whole document EXCEPT its frontmatter changelog (historical entries may quote the wording a fix removed)
    hits = {p: len(re.findall(r"(?i)\bthe eight gates\b", _without_changelog(d.front(p)) + d.body(p))) for p in files}
    return _verdict(b, "the gate set is nine; these surfaces still say eight", {p: n for p, n in hits.items() if n},
                    files_checked=len(files))


def _regex_cell(binds, path, pattern, reason, d, flags=0):
    t = d.body(path)
    if t is None:
        return _um(binds, f"not readable at ref: {path}")
    n = len(re.findall(pattern, t, flags))
    return _verdict(binds, reason, {path: n} if n else {})


def t5_t4_heading(d, facts):
    return _regex_cell(["V2", "R64"], T4_DOC, r"(?m)^#{2,4}\s*4\.2\b[^\n]*\bthe six checks\b",
                       "T4 4.2 heading still counts six checks", d)


def t5_tracker_comment(d, facts):
    return _regex_cell(["V4", "R66"], TRACKER_REL, r"Eight, not thirty-three", "tracker comment still says Eight", d)


def t5_gate_map(d, facts):
    return _regex_cell(["V5", "R67"], T3_DOC, r"eight-row map", "T3 5.4 test 5 still says an eight-row map", d)


def t5_spelling(d, facts):
    b = ["V6", "R68"]
    miss = _missing([T3_DOC, T4_DOC], d)
    if miss:
        return _um(b, "not readable at ref: " + ",".join(miss))
    hits = {}
    for p in (T3_DOC, T4_DOC):
        n = len(re.findall(r"NO DETECTOR", d.body(p)))
        if n:
            hits[p + " [NO DETECTOR]"] = n
    n = len(re.findall(r"\bNA if never run\b", d.body(T4_DOC)))
    if n:
        hits[T4_DOC + " [bare NA]"] = n
    return _verdict(b, "verdict spelling drifts from the closed set (NO_DETECTOR, N/A)", hits)


def t5_l0_denominator(d, facts):
    return _regex_cell(["V7", "R69"], L0_DOC, r"0/320|\b320 gates\b", "L0 instance still carries the eight-gate denominator", d)


def t5_review_record(d, facts):
    b = ["V10", "R72"]
    t = d.text(T1_DOC)
    if t is None:
        return _um(b, f"not readable at ref: {T1_DOC}")
    targets = []
    m = re.search(r"(?m)^review_record:\s*(\S+)", t)
    if m:
        targets = [m.group(1)]
    else:
        dm = re.search(r"(?ms)^document_reviews:\s*\n((?:[ \t]+-[^\n]*\n)+)", t)
        if dm:
            targets = [x.strip() for x in re.findall(r"-\s*(\S+)", dm.group(1))]
    if not targets:
        return mk("measurement", "NO_DETECTOR", "T1 carries neither a review_record nor a document_reviews pointer", binds=b)
    missing = [x for x in targets if not d.rp.exists(P + x)]
    return _verdict(b, "T1 names a review file that does not exist at ref", missing, targets=sorted(targets))


def t5_t2_review_counts(d, facts):
    b = ["V11", "R73"]
    fm = d.front(T2_DOC)
    if fm is None:
        return _um(b, f"not readable at ref: {T2_DOC}")
    hits = [ln.strip()[:120] for ln in fm.split("\n")
            if "REVIEW_DATA_PLANE_v3_0" in ln and re.search(r"10 MAJOR \+ 11 MINOR", ln)]
    return _verdict(b, "T2 document_reviews miscounts the v3.0 review's findings (the review file has 9 MAJOR + 10 MINOR)", hits)


def t5_t2_elements(d, facts):
    b = ["V13", "R75"]
    fm = d.front(T2_DOC)
    if fm is None:
        return _um(b, f"not readable at ref: {T2_DOC}")
    # the register's remedy: "ten elements", or annotate that 1b was added after the entry was written
    hits = [ln.strip()[:120] for ln in fm.split("\n")
            if re.search(r"§13\.3 is nine elements", ln) and not re.search(r"ten elements|\b1b\b", ln)]
    return _verdict(b, "T2 changelog item (f) says nine elements; 13.3 has ten", hits)


def t5_transfers(d, facts):
    b = ["V9", "R71"]
    t3, t2 = d.body(T3_DOC), d.body(T2_DOC)
    if t3 is None or t2 is None:
        return _um(b, "T2 or T3 not readable at ref")
    if not re.search(r"\*\*Presentation parity\*\*\s+holds", t3):
        return mk("measurement", "PASS", None, binds=b)
    line = next((ln for ln in t2.split("\n") if "Presentation parity" in ln), None)
    if line is None:
        return mk("measurement", "NO_DETECTOR", "T3 demands Presentation parity but T2 carries no such row", binds=b)
    if "[TRANSFERS]" in line:
        return mk("measurement", "FAIL", "T3 5.4 test 4 requires what T2 marks [TRANSFERS] and forbids a layer plan to inherit", binds=b)
    return mk("measurement", "PASS", None, binds=b)


def tracker_gates(src):
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "GATES" for t in node.targets) \
                and isinstance(node.value, (ast.List, ast.Tuple)):
            out = []
            for e in node.value.elts:
                if isinstance(e, (ast.Tuple, ast.List)) and e.elts and isinstance(e.elts[0], ast.Constant) and isinstance(e.elts[0].value, str):
                    out.append(e.elts[0].value)
                else:
                    return None
            return out
    return None


def t5_gate_set(d, facts):
    b = ["V1", "R63"]   # gate NAMES only: R65 (the six-vs-nine static-check count) and R67 are separate rows with their own text detectors
    if facts is None:
        return _um(b, "inspector registry not readable at ref")
    src = d.text(TRACKER_REL)
    if src is None:
        return _um(b, f"not readable at ref: {TRACKER_REL}")
    gates = tracker_gates(src)
    if gates is None:
        return _um(b, "tracker GATES could not be parsed")
    inspector = list(facts["cell_gates"])
    problems = {}
    if gates != inspector:
        problems["tracker_vs_inspector"] = dict(tracker=gates, inspector=inspector)
    for name, path in (("T4_section_4", T4_DOC), ("T3_section_5_2", T3_DOC)):
        t = d.text(path)
        if t is None:
            return _um(b, f"not readable at ref: {path}")
        absent = [g for g in inspector if not re.search(r"(?m)^\|\s*\*\*" + re.escape(g) + r"\*\*", t)]
        if absent:
            problems[name] = dict(missing_gate_rows=absent)
    return _verdict(b, "the gate set differs across surfaces", problems, gates=len(inspector))


def t5_manifest_root(d, facts):
    b = ["V14", "manifest_fingerprint --check"]
    t = d.text(MANIFEST_REL)
    if t is None:
        return _um(b, f"not readable at ref: {MANIFEST_REL}")
    try:
        m = json.loads(t)
    except ValueError:
        return _um(b, "manifest is not JSON")
    entries = m.get("entries")
    if not isinstance(entries, list):
        return _um(b, "manifest has no entries list")
    blob = json.dumps(entries, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    observed = hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]
    ok = observed == m.get("fingerprint") and m.get("entry_count") == len(entries)
    extra = dict(declared=m.get("fingerprint"), observed=observed, entries=len(entries), entry_count_declared=m.get("entry_count"))
    if ok:
        return mk("measurement", "PASS", None, binds=b, **extra)
    return mk("measurement", "FAIL", "manifest root fingerprint or entry_count does not reproduce", binds=b, **extra)


TIER_IDS = {T1_DOC: "PRODUCT_DEFINITION", T2_DOC: "DATA_PLANE_VALUE_ARCHITECTURE", T3_DOC: "LAYER_DEFINITION_AND_STRATEGY_TEMPLATE",
            T4_DOC: "ASSET_ELEVATION_TEMPLATE", L0_DOC: "L0_BRAHMAGYAN_STRATEGY"}


def t5_manifest_tiers(d, facts):
    b = ["V14", "R82"]
    t = d.text(MANIFEST_REL)
    if t is None:
        return _um(b, f"not readable at ref: {MANIFEST_REL}")
    try:
        entries = json.loads(t).get("entries", [])
    except ValueError:
        return _um(b, "manifest is not JSON")
    found, bad = 0, {}
    for path in TIER_IDS:
        for e in entries:
            if not isinstance(e, dict) or e.get("path") != path:
                continue
            declared = e.get("fingerprint_sha256") or e.get("fingerprint")
            actual = d.rp.sha256(path)
            if declared is None or actual is None:
                continue
            found += 1
            if declared != actual:
                bad[path] = dict(declared=str(declared)[:16], on_disk=actual[:16])
    if found == 0:
        return mk("measurement", "NO_DETECTOR", "the manifest at ref carries no fingerprinted entry for the Nikasha tier documents", binds=b)
    return _verdict(b, "a tier document's manifest fingerprint differs from its blob at ref", bad, entries_checked=found)


def t5_ledger_criteria(d, facts):
    b = ["R251"]
    text = d.text(GAPS_REL)
    if text is None:
        return _um(b, f"not readable at ref: {GAPS_REL}")
    if facts is None:
        return _um(b, "inspector registry not readable at ref")
    known = set(facts["criteria"]) | set(facts["retired"])
    crits = sorted({r["criterion"] for r in parse_ledger(text) if isinstance(r.get("criterion"), str)})
    unknown = [c for c in crits if c not in known]
    if unknown:
        return mk("measurement", "FAIL", f"{len(unknown)} ledger criterion string(s) are not in the inspector's registry", binds=b,
                  unregistered_count=len(unknown), unregistered_sample=unknown[:10], criteria_in_ledger=len(crits))
    return mk("measurement", "PASS", None, binds=b, criteria_in_ledger=len(crits))


def t5_ledger_states(d, facts):
    b = ["T5 ledger state vocabulary"]
    text = d.text(GAPS_REL)
    if text is None:
        return _um(b, f"not readable at ref: {GAPS_REL}")
    states = sorted({str(r.get("state", "OPEN")).upper() for r in parse_ledger(text)})
    unknown = [s for s in states if s not in LEDGER_STATES]
    return _verdict(b, "ledger rows carry a state outside OPEN|IN_PROGRESS|CLOSED|WITHDRAWN", unknown, states=states)


def t5_drift(d, facts):
    return mk("measurement", "UNMEASURED",
              "drift_detector.py's schema axis reads a database; run it in CI (E1.7)", binds=["drift_detector"])


T5_DETECTORS = (
    ("eight_gates_text", t5_eight_gates), ("t4_heading_checks", t5_t4_heading), ("tracker_comment", t5_tracker_comment),
    ("t3_gate_map_count", t5_gate_map), ("verdict_spelling", t5_spelling), ("l0_denominator", t5_l0_denominator),
    ("t1_review_record", t5_review_record), ("t2_review_counts", t5_t2_review_counts), ("t2_element_count", t5_t2_elements),
    ("transfers_contradiction", t5_transfers), ("gate_set_agreement", t5_gate_set),
    ("manifest_root_fingerprint", t5_manifest_root), ("manifest_tier_entries", t5_manifest_tiers),
    ("ledger_criteria_registered", t5_ledger_criteria), ("ledger_state_vocabulary", t5_ledger_states),
    ("drift_detector", t5_drift),
)


# ───────────────────────────── engine_build_checks ─────────────────────────────

def engine_build_checks(facts, census, fresh):
    if facts is None:
        return {}
    out = {}
    for crit in sorted(c for c, e in facts["criteria"].items() if e.get("gate") == "Build"):
        def fn(docs, crit=crit):
            vs = [(a.get("measurements") or {}).get(crit, {}).get("v") for d in docs.values() for a in d["assets"]]
            vs = [v for v in vs if v is not None]
            if not vs:
                return "UNMEASURED", "no cell", {}
            if "FAIL" in vs or "ERRORED" in vs:
                return "FAIL", None, {}
            if "NO_DETECTOR" in vs:
                return "NO_DETECTOR", None, {}
            if "PARTIAL" in vs:
                return "PARTIAL", None, {}
            return "PASS", None, {}
        out[crit] = from_census(census, fresh, LAYERS, fn)["verdict"]
    return out


# ───────────────────────────── the scorecard ─────────────────────────────

def test_detail(name, verdict, cells):
    """The verdict with its qualifier spelled out: a T1 that passes on declarations says how many ("PASS, 2 declared
    unplantable"), never a bare PASS."""
    if name == "T1" and verdict == "PASS":
        n = cells.get("plant_suite", {}).get("declared_unplantable_count", 0)
        if n:
            return f"PASS, {n} declared unplantable"
    return verdict


def fail_basis(cells):
    """Why a test reads FAIL: a measured defect, or only a known-defect register row still open. None unless FAIL."""
    meas = sorted(n for n, c in cells.items() if c["kind"] == "measurement" and c["verdict"] == "FAIL")
    pre = sorted(n for n, c in cells.items() if c["kind"] == "precondition" and c["verdict"] == "FAIL")
    if not meas and not pre:
        return None
    parts = []
    if meas:
        parts.append("measured: " + ", ".join(meas))
    if pre:
        parts.append("precondition: " + ", ".join(f"{n} ({', '.join(cells[n].get('open', []))} open)" for n in pre))
    return "; ".join(parts)


def build_scorecard(repo, ref, census_dir=None, t1_evidence=None):
    repo = str(repo)
    assert_not_shallow(repo)
    sha = resolve_ref(repo, ref)
    rp = RepoAt(repo, sha)
    rp.prefetch([INSPECTOR_REL, REGISTER_REL, GAPS_REL, CERTS_REL, T1_DOC, T2_DOC, T3_DOC, T4_DOC, L0_DOC, TRACKER_REL,
                 MANIFEST_REL, GEN_REL, *[x for x in rp.list(PILOT_DIR) if x.endswith(".md")]])
    gen_bytes = Path(__file__).read_bytes()
    facts = registry_facts(rp)
    inspector_blob = rp.sha256(INSPECTOR_REL)
    census = load_census(_census_items_from_dir(census_dir) if census_dir is not None else _census_items_from_repo(rp))
    fresh = {lyr: freshness(e, facts, rp) for lyr, e in census.items()}
    ev = load_t1_evidence(t1_evidence)

    reg_text = rp.text(REGISTER_REL)
    reg = parse_register(reg_text) if reg_text is not None else None
    ver = re.search(r'(?m)^version:\s*"?([^"\n]+)"?', reg_text or "")

    # T1
    plant, mut, n_plants = t1_cells(ev, facts, inspector_blob, rp)
    t1 = {"plant_suite": plant, "mutation_notice": mut, "known_defect_rows": known_defect_cell("T1", reg)}
    required = sorted(c for c, e in (facts or {"criteria": {}})["criteria"].items() if e.get("detector") == MEASURE_DETECTOR)

    # T2
    t2 = {
        "build_registered_rederivation": from_census(census, fresh, LAYERS, t2_rederive(rp)),
        "handverify_sample": mk("measurement", "NO_DETECTOR",
                                "the stratified production hand-verification (T2_PROTOCOL.md) has no machine detector; the other "
                                "checks need production count_sql and build history"),
        "known_defect_rows": known_defect_cell("T2", reg),
    }

    # T3
    t3, gap_ids = t3_cells(rp, census, fresh)
    t3["known_defect_rows"] = known_defect_cell("T3", reg)

    # T4
    t4 = {lyr: from_census(census, fresh, (lyr,), t4_layer) for lyr in T4_LAYERS}
    t4["production_provenance"] = mk("measurement", "NO_DETECTOR",
                                     "the census JSON records no database identity: 'ran in production' is not provable from it")
    t4["known_defect_rows"] = known_defect_cell("T4", reg)

    # T5
    d = Docs(rp)
    t5 = {name: fn(d, facts) for name, fn in T5_DETECTORS}
    t5["known_defect_rows"] = known_defect_cell("T5", reg)

    assets_total = sum(len(e["doc"]["assets"]) for e in census.values())
    populations = {
        "T1": f"{len(required)} registry check(s) with detector {MEASURE_DETECTOR} at registry revision "
              f"{facts['revision'] if facts else 'unknown'}; {n_plants if n_plants is not None else 0} plant(s) supplied",
        "T2": f"census layers L0-L5 ({len([lyr for lyr in LAYERS if lyr in census])} of 6 supplied, {assets_total} assets); "
              f"@register decorators scanned (AST) under {WRITERS_PREFIX}",
        "T3": f"{gap_ids if gap_ids is not None else 'unreadable'} gap id(s) in {GAPS_REL}",
        "T4": "census layers L1-L5, active population per layer",
        "T5": f"tiers T1-T4, L0 instance, {len(d.pilots())} pilot(s), tracker, ledgers, manifest at the ref",
    }
    evidence = {
        "T1": ("t1_evidence (sha256 in inputs)" if ev else None),
        "T2": "census_L*.json + " + WRITERS_PREFIX,
        "T3": GAPS_REL,
        "T4": "census_L1..L5.json",
        "T5": N + " (tier documents), " + TRACKER_REL + ", " + MANIFEST_REL,
    }
    tests = {}
    for name, cells in (("T1", t1), ("T2", t2), ("T3", t3), ("T4", t4), ("T5", t5)):
        tests[name] = {
            "verdict": combine(cells),
            "detail": test_detail(name, combine(cells), cells),
            "fail_basis": fail_basis(cells),
            "definition": DEFINITIONS[name],
            "population": populations[name],
            "evidence": evidence[name],
            "cells": cells,
            "unmeasured_cells": sorted(n for n, c in cells.items() if c["verdict"] in ("UNMEASURED", "NO_DETECTOR")),
        }

    card = {
        "schema": SCHEMA,
        "generator": GEN_REL,
        "generator_sha256": hashlib.sha256(gen_bytes).hexdigest(),
        "generator_at_ref_sha256": rp.sha256(GEN_REL),
        "generator_matches_ref": (None if rp.sha256(GEN_REL) is None else rp.sha256(GEN_REL) == hashlib.sha256(gen_bytes).hexdigest()),
        "inspector": INSPECTOR_REL,
        "inspector_commit": rp.last_commit(INSPECTOR_REL),
        "inspector_blob_sha256": inspector_blob,
        "ref": sha,
        "registry": {"revision": facts["revision"] if facts else None, "fingerprint": facts["fingerprint"] if facts else None},
        "change_register": {"path": REGISTER_REL, "version": ver.group(1).strip() if ver else None, "sha256": rp.sha256(REGISTER_REL)},
        "measured_offline": True,
        "vocabulary": {"verdicts": list(VERDICTS),
                       "extension": "Track E section 5 names PASS|FAIL|PARTIAL; NO_DETECTOR (no offline detector exists for the "
                                    "claim) and UNMEASURED (an input is missing or stale) extend it and are never a pass"},
        "inputs": {
            "census": [dict(layer=lyr, sha256=e["sha256"], generated=e["doc"].get("generated"),
                            tool_commit=e["doc"].get("tool_commit"), tool_dirty=e["doc"].get("tool_dirty"),
                            declarations_sha256=e["doc"].get("declarations_sha256"),
                            registry_revision=e["doc"].get("registry_revision"),
                            registry_fingerprint=e["doc"].get("registry_fingerprint"),
                            fresh=fresh[lyr][0], **({} if fresh[lyr][0] else {"stale_reason": fresh[lyr][1]}))
                       for lyr, e in sorted(census.items())],
            "ledger_gaps_sha256": rp.sha256(GAPS_REL),
            "ledger_certs_sha256": rp.sha256(CERTS_REL),
            "t1_evidence": ({"sha256": ev["sha256"]} if ev else None),
        },
        "tests": tests,
        "engine_build_checks": engine_build_checks(facts, census, fresh),
        "engine_claims_not_covered": list(ENGINE_CLAIMS_NOT_COVERED),
    }
    warnings = []
    if card["generator_matches_ref"] is False:
        warnings.append("the generator that produced this scorecard differs from the generator blob at the ref")
    card["summary"] = {
        "warnings": warnings,
        "verdicts": {n: t["verdict"] for n, t in tests.items()},
        "details": {n: t["detail"] for n, t in tests.items()},
        "all_tests_pass": all(t["verdict"] == "PASS" for t in tests.values()),
        "t1_declared_unplantable": int(tests["T1"]["cells"].get("plant_suite", {}).get("declared_unplantable_count", 0)
                                       if tests["T1"]["verdict"] == "PASS" else 0),
        "all_tests_pass_note": "all_tests_pass can be true while T1 reads 'PASS, N declared unplantable': N checks are covered by "
                               "a re-tested declaration, not by a plant. Read t1_declared_unplantable (and details) before "
                               "treating all_tests_pass as unqualified",
        "unmeasured_cells_total": sum(len(t["unmeasured_cells"]) for t in tests.values()),
        "note": "measured offline from saved evidence; UNMEASURED and NO_DETECTOR are never a pass",
    }
    return card


def render(card):
    return json.dumps(card, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


# ───────────────────────────── CLI ─────────────────────────────

def _diff_names(old, new):
    names = []
    for k in sorted(set(old) | set(new)):
        if old.get(k) != new.get(k):
            if k == "tests":
                for t in sorted(set(old.get(k, {})) | set(new.get(k, {}))):
                    if old.get(k, {}).get(t) != new.get(k, {}).get(t):
                        names.append(f"tests.{t}")
            else:
                names.append(k)
    return names


def main(argv=None):
    ap = argparse.ArgumentParser(description="E1.1 T1-T5 scorecard (offline, read-only, deterministic)")
    ap.add_argument("--repo", default=None, help="git repository (default: the one containing the current directory)")
    ap.add_argument("--ref", default=None, help="git ref to measure (default HEAD; --check: the committed file's recorded ref)")
    ap.add_argument("--census-dir", default=None,
                    help="directory of census JSON (default: the censuses committed under 00_ARCHITECTURE/control/census, "
                         "read at the ref, so --check works from repository contents alone)")
    ap.add_argument("--t1-evidence", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    try:
        repo = args.repo
        if repo is None:
            p = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
            repo = p.stdout.strip()
            if p.returncode != 0 or not repo:
                raise ScorecardError("not inside a git repository (use --repo)")
        out = Path(args.out) if args.out else Path(repo) / OUT_REL
        if args.check:
            try:
                committed_text = out.read_text(encoding="utf-8")
                committed = json.loads(committed_text)
            except (OSError, ValueError) as exc:
                raise ScorecardError(f"cannot read the committed scorecard {out}: {exc}")
            if not isinstance(committed, dict) or committed.get("schema") != SCHEMA:
                raise ScorecardError(f"{out} is not a scorecard (no schema {SCHEMA!r}); --out names the committed scorecard file")
            ref = args.ref or committed.get("ref")
            if not ref:
                raise ScorecardError("committed scorecard records no ref")
            ins = committed.get("inputs") or {}
            if ins.get("t1_evidence") and not args.t1_evidence:
                raise ScorecardError("the committed scorecard used T1 evidence: supply --t1-evidence")
            fresh_card = build_scorecard(repo, ref, args.census_dir, args.t1_evidence)
            fresh_text = render(fresh_card)
            if fresh_text == committed_text:
                print(f"nikasha_scorecard: {out} matches a fresh recompute at {fresh_card['ref'][:12]}")
                return 0
            names = _diff_names(committed, fresh_card)
            print("nikasha_scorecard: MISMATCH -- the committed scorecard differs from a fresh recompute in: "
                  + (", ".join(names) or "formatting"))
            return 2
        if out.exists():
            try:
                prior = json.loads(out.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                prior = None
            if not isinstance(prior, dict) or prior.get("schema") != SCHEMA:
                raise ScorecardError(f"refusing to overwrite {out}: it exists and is not a {SCHEMA} scorecard")
        card = build_scorecard(repo, args.ref or "HEAD", args.census_dir, args.t1_evidence)
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_name(out.name + ".tmp")
        tmp.write_text(render(card), encoding="utf-8")
        os.replace(tmp, out)
        for name in ("T1", "T2", "T3", "T4", "T5"):
            t = card["tests"][name]
            print(f"{name}  {t['detail']:<10} unmeasured/no-detector cells: {', '.join(t['unmeasured_cells']) or '-'}")
        print(f"ref {card['ref'][:12]}  registry rev {card['registry']['revision']}  wrote {out}")
        return 0
    except ScorecardError as exc:
        print(f"nikasha_scorecard: {exc}", file=sys.stderr)
        return 5


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"nikasha_scorecard: script error -- {exc}", file=sys.stderr)
        sys.exit(5)
