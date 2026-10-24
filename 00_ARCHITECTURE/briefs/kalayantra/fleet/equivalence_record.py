#!/usr/bin/env python3
"""EQUIVALENCE_RECORD/1 — the canonical G-8 equivalence record, the explicit trial projection and the EQ_CHECK decision
(SCORING PLAN A10.1 §3, amendment A10.1 B1). Commit SHA equality is neither required nor sufficient: this record is what lets the
squash-merged main dispatch head inherit the integration head's qualifying trial.

    python3 equivalence_record.py record  --repo <git repo> --commit <rev> --pinned-inputs <file> --out <record.json> [--generated-at <ISO UTC>]
    python3 equivalence_record.py compare --trial <record.json> --main <record.json> [--out <decision.json>] [--table <requalification.json>]

`record` reads repository BYTES at the commit (git objects, nothing checked out) and the pinned-inputs file; no database, no network, no write
outside --out and its `.manifests` folder. `compare` writes the §3.4 decision and never changes a record. Exit codes — record: 0 complete,
2 written but INCOMPLETE (a category is null, N.7.6), 1 refused (nothing written); compare: 0 EQUAL, 3 DIFFERS, 1 a record was refused.

THE RECORD (§3.1) — one canonical JSON document (UTF-8, keys sorted, no insignificant whitespace, arrays in their governed order, REAL values as
the decimal strings the writers persist; a float anywhere is refused). Five equality categories, each with `digest = sha256(canonical subtree)`,
`parts` (sha256 of each named part of the subtree, so a difference can be attributed) and a retained UNNORMALIZED manifest beside the record
(`<out>.manifests/E?.json`: the record only indexes it); `record_digest = sha256(canonical [E1..E5 digests])`; one provenance block E6, stored and
never compared. A category that cannot be read from its sources is NULL with the reasons listed — never a default (N.7.6); the record is then
`complete: false` and the comparison cannot read EQUAL.

    E1 Code      every result-bearing module with its import closure: the IMPLEMENTATION_MODULES lists (read by a restricted AST evaluator from
                 input_vector.py AT THE COMMIT), the source digest of each listed module (the same rule as input_vector._module_source_digest), the
                 writer's static import closure (a port of tests/l3/gochara/_import_closure.py against the commit's bytes; a closure module in no
                 list REFUSES the record), the required result-bearing modules (window_solver, window_solver_check: present in the tree but in no
                 list REFUSES), the qualification CHECK function bodies in the migrations. The pinned input vector's `implementation` stage
                 digests must equal the ones recomputed from the commit's bytes, else the pinned inputs are not of this commit (REFUSED).
    E2 Rules     registry digest + census, selection/profile flags, rulings digest, the qualification table and result policy, convention content
                 (zodiac, ayanamsha, node model, epoch), BOTH orb policies, declared accuracy.
    E3 Inputs    E3a = the projection the trial's classes consumed (L0 loader digests and row CONTENT digests, copied L1 facts, the Vimshottari
                 population and held state, AV declarations) — compared. E3b = the complete century snapshot population — bound by digest per
                 row at dispatch, checked only for COVERAGE of every E3a row, never claimed proven by the trial.
    E4 Runtime   Swiss library version and binary sha, sha256 of every ephemeris file opened, the series probe, OS/arch, Python, dependency lock.
                 Only a `qualifying_run` (linux/amd64) or a `dispatch_image` has an E4; a `rolling_diagnostic` run has none (P3/P6).
    E5 Config    the CENTURY fields declared in the dispatch config (horizon and basis, final-rule selection, result policy, deferral, budgets, class
                 universe, verification plan) and the tolerances read from the module constants.
    E6 Provenance commit and tree, branch, image tag/digest, CI and dispatch run ids, manifest ids, overlay hashes, timestamps. Never compared.

THE PROJECTION (§3.3) — the ONLY fields a 12-class trial may differ in, excluded by name in `projection.excluded_fields` (PROJECTION_EXCLUDED, a
fixed list; a record carrying any other list is refused): the trial's own stored_scope, test_slice, horizon, horizon_basis and class subset. Their
values are kept only as sha256 (a horizon basis names a dated life event; no personal datum enters the record). A trial-scope key inside the
century config is refused (P1: the manifest would be unsealable). P5: the classes outside the trial are DISCLOSED in the projection.

PINNED INPUTS (`ky.eq_pinned_inputs/1`, what the repository cannot say; produced by the trial harness / the dispatch dry run). Closed keys:
  input_vector     REQUIRED. The stored `ka_gochara_input_vector/3` of the generation (services.gochara_kernel.input_vector), keys closed.
  rules            {selection: {selected_rule_version, profile}, declared_accuracy: {...}}
  inputs           {e3a: {l0_rows: {asset: {row_id: content}}, l1_facts: {fact_id: {content, provenance}}, dasha: {population: {row_id: content},
                   held_state: content}, av_declarations: {id: content}}, e3b_population: {row_key: content}} with row keys
                   `l0:<asset>:<id>` · `l1:<id>` · `dasha:population:<id>` · `dasha:held_state` · `av:<id>`
  century_config   {stored_scope, horizon: {start, end}, horizon_basis, final_rules, result_policy, in_build_verify, budgets: {per_window,
                   verifier}, classes: [...], verification_plan: {mode, shard_plan_digest, g6_sampling_rule, seed_rule}}
  runtime          {kind: qualifying_run|dispatch_image|rolling_diagnostic, arch, python, dependency_lock_digest}
                   an EMULATED qualifying run (SR-T24-AMD64-DOCKER: linux/amd64 container on an arm64 Mac) adds `emulated: true` and `arch_probe` {source: in_container, uname_machine: x86_64,
                   platform_machine, sys_platform: linux}: the arch is READ inside the container, never asserted from outside; it is refused without the probe and without the emulation
                   note `provenance.platform_notes.emulation` {emulated: true, layer: rosetta|qemu|undetermined}.  The note lives in E6 (never compared): emulation does not change E4.
  trial_scope      {horizon} (the trial's own; excluded by name)
  provenance       {branch, image_tag, image_digest, ci_run_ids, dispatch_run_id, manifest_ids, overlay_hashes, platform_notes}
JSON numbers with a fraction or exponent are read as their source TEXT (the decimal string as persisted); a NaN/Infinity is refused.

THE DECISION (§3.4) `ky.equivalence_decision/1` = {trial_record_sha, main_record_sha, per_category, decision: EQUAL|DIFFERS, action}: EQUAL needs E1..E5
digests equal and the E3b coverage of every trial E3a row; E6 is stored beside, not compared. It never relabels the producing commit or image and never
rewrites an attestation: both E6 blocks are copied verbatim into `provenance`, and a record file is only ever read. The minimum action per difference
is DATA (equivalence_requalification.json, §3.5), chosen by the differing parts.
"""
from __future__ import annotations

import argparse
import ast
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

FLEET = Path(__file__).resolve().parent
SCHEMA = "ky.equivalence_record/1"
DECISION_SCHEMA = "ky.equivalence_decision/1"
PINNED_SCHEMA = "ky.eq_pinned_inputs/1"
TABLE_SCHEMA = "ky.equivalence_requalification/1"
TABLE_PATH = FLEET / "equivalence_requalification.json"

CATEGORIES = ("E1", "E2", "E3", "E4", "E5")
SIDECAR = "platform/python-sidecar"
KERNEL = SIDECAR + "/services/gochara_kernel"
INPUT_VECTOR_REL = KERNEL + "/input_vector.py"
RESULT_POLICY_REL = KERNEL + "/result_policy.py"
CONVENTION_REL = KERNEL + "/convention.py"
RECORD_STORE_REL = KERNEL + "/record_store.py"
REQUIREMENTS_REL = SIDECAR + "/requirements.txt"
MIGRATIONS = "platform/migrations/"
WRITER_MODULE = "pipeline.orchestrator.writers.ka_gochara_v5"
CLOSURE_ROOTS = ("services.gochara_kernel", "services.gochara_rules")
#: modules whose edit moves a result and which the lists MUST carry as soon as they exist (T19; A10.1 B1)
REQUIRED_RESULT_BEARING = ("services.gochara_kernel.window_solver", "services.gochara_kernel.window_solver_check")
QUALIFICATION_CHECK_FUNCTION = "ka_gochara_window_qualification_ok"
QUALIFICATION_CHECK_FIRST_MIGRATION = 1240
#: tolerance name -> the constant names that may carry it, resolved over the E1 module set (an unresolved or ambiguous one makes E5 null)
TOLERANCES = {
    "TIE": ("TIE", "TIE_TOLERANCE"), "GREY": ("GREY", "GREY_BAND"), "LEAF_S": ("LEAF_S",), "BISECT_SECONDS": ("BISECT_SECONDS",),
    "F4_ABS_SLACK": ("F4_ABS_SLACK",), "MIN_EXCURSION_SECONDS": ("MIN_EXCURSION_SECONDS",), "ISOLATION_S": ("ISOLATION_S",),
    "MAX_EVALS": ("MAX_EVALS",),
}
#: §3.3 P1 — the ONLY fields excluded from the comparison, by name
PROJECTION_EXCLUDED = ("trial.class_subset", "trial.horizon", "trial.horizon_basis", "trial.stored_scope", "trial.test_slice")
RUNTIME_KINDS = ("qualifying_run", "dispatch_image", "rolling_diagnostic")
QUALIFYING_ARCH = "linux/amd64"
CENTURY_STORED_SCOPE = "stored_non_moon"

VECTOR_SCHEMA = "ka_gochara_input_vector/3"
VECTOR_REQUIRED = ("schema", "stored_scope", "result_policy", "sky_convention", "registry", "node", "ephemeris", "l0", "orb_policy",
                   "rulings_digest", "implementation")
# `scored_until`: services/gochara_kernel/input_vector.py SCORED_UNTIL_KEY (D-FLIP F-10, lane od1-scored-until) - the exclusive end of the scored horizon, serialised
# additively when the vector is built with it; the same closed list as the serializer's optional keys.
VECTOR_OPTIONAL = ("scored_classes", "in_build_verify", "test_slice", "horizon_basis", "scored_until", "near_miss_layer_version", "qualification_table")
EPHEMERIS_KEYS = ("backend", "swe_version", "library_sha256", "platform", "files", "probe_digest")
PINNED_KEYS = ("schema", "input_vector", "rules", "inputs", "century_config", "runtime", "trial_scope", "provenance")
CENTURY_KEYS = ("stored_scope", "horizon", "horizon_basis", "final_rules", "result_policy", "in_build_verify", "budgets", "classes",
                "verification_plan")
TRIAL_SCOPE_KEYS = ("test_slice", "trial_scope", "class_subset", "scored_classes", "trial")
PROVENANCE_KEYS = ("branch", "image_tag", "image_digest", "ci_run_ids", "dispatch_run_id", "manifest_ids", "overlay_hashes", "platform_notes")
EMULATION_LAYERS = ("rosetta", "qemu", "undetermined")


class EqrRefusal(RuntimeError):
    """The record (or the decision) cannot be produced: nothing is written, nothing is guessed (B.10)."""


class Unreadable(Exception):
    """A part cannot be read from its sources: the category is NULL, the reason is listed (N.7.6)."""


# ── canonical serialization (§3.1) ──────────────────────────────────────────────────────────────────────────────────────────────────────

def _no_floats(o, path="$"):
    if isinstance(o, float):
        raise EqrRefusal(f"{path}: a float is not a canonical number — REAL values are decimal strings")
    if isinstance(o, dict):
        for k, v in o.items():
            if not isinstance(k, str):
                raise EqrRefusal(f"{path}: a non-string key {k!r}")
            _no_floats(v, f"{path}.{k}")
    elif isinstance(o, (list, tuple)):
        for i, v in enumerate(o):
            _no_floats(v, f"{path}[{i}]")


def canonical_json(o) -> str:
    _no_floats(o)
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha(o) -> str:
    return sha_bytes(canonical_json(o).encode("utf-8"))


def _refuse_constant(c):
    raise EqrRefusal(f"JSON constant {c} is not a canonical number")


def loads(data: bytes, what: str):
    try:
        return json.loads(data.decode("utf-8"), parse_float=str, parse_constant=_refuse_constant)
    except (UnicodeDecodeError, ValueError) as exc:
        raise EqrRefusal(f"{what}: not valid UTF-8 JSON ({exc})") from exc


# ── the commit's bytes ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────

class DirTree:
    """A directory standing for a commit's tree (tests and a clean checkout)."""
    commit = tree = None

    def __init__(self, root):
        self.root = Path(root)
        self._cache: dict = {}

    def exists(self, rel: str) -> bool:
        return (self.root / rel).is_file()

    def read(self, rel: str) -> bytes:
        if rel not in self._cache:
            try:
                self._cache[rel] = (self.root / rel).read_bytes()
            except OSError as exc:
                raise EqrRefusal(f"{rel}: not readable in the tree ({exc})") from exc
        return self._cache[rel]

    def list_files(self, prefix: str) -> list:
        base = self.root / prefix
        return sorted(str(p.relative_to(self.root)) for p in base.rglob("*") if p.is_file()) if base.is_dir() else []


def _git_env() -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") or k == "GIT_CEILING_DIRECTORIES"}
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return env


def _git(repo, *args) -> bytes:
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, timeout=120, env=_git_env())
    if p.returncode != 0:
        raise EqrRefusal(f"git {' '.join(args[:2])} failed: {p.stderr.decode('utf-8', 'replace').strip()[:200]}")
    return p.stdout


class GitTree:
    """The bytes of one commit, read from git objects (read-only git; nothing is checked out)."""

    def __init__(self, repo, rev: str):
        self.repo = repo
        self.commit = _git(repo, "rev-parse", "--verify", "--quiet", rev + "^{commit}").decode().strip()
        self.tree = _git(repo, "rev-parse", "--verify", "--quiet", self.commit + "^{tree}").decode().strip()
        self._paths = {p.decode("utf-8") for p in _git(repo, "ls-tree", "-r", "-z", "--name-only", self.commit).split(b"\0") if p}
        self._cache: dict = {}

    def exists(self, rel: str) -> bool:
        return rel in self._paths

    def read(self, rel: str) -> bytes:
        if rel not in self._cache:
            if rel not in self._paths:
                raise EqrRefusal(f"{rel}: not in commit {self.commit[:12]}")
            self._cache[rel] = _git(self.repo, "cat-file", "blob", f"{self.commit}:{rel}")
        return self._cache[rel]

    def list_files(self, prefix: str) -> list:
        return sorted(p for p in self._paths if p.startswith(prefix))

    def prefetch(self, rels) -> None:
        """Read many blobs in ONE git process (`cat-file --batch`)."""
        todo = [r for r in rels if r in self._paths and r not in self._cache]
        if not todo:
            return
        p = subprocess.run(["git", "-C", str(self.repo), "cat-file", "--batch"], input="".join(f"{self.commit}:{r}\n" for r in todo).encode(),
                           capture_output=True, timeout=300, env=_git_env())
        if p.returncode != 0:
            raise EqrRefusal(f"git cat-file --batch failed: {p.stderr.decode('utf-8', 'replace').strip()[:200]}")
        buf, pos = p.stdout, 0
        for r in todo:
            end = buf.index(b"\n", pos)
            _sha, kind, size = buf[pos:end].decode().split()
            if kind != "blob":
                raise EqrRefusal(f"{r}: not a blob")
            self._cache[r] = buf[end + 1:end + 1 + int(size)]
            pos = end + 1 + int(size) + 1


def _text(tree, rel: str) -> str:
    """`Path.read_text` as input_vector reads a module: UTF-8, universal newlines."""
    try:
        return tree.read(rel).decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    except UnicodeDecodeError as exc:
        raise EqrRefusal(f"{rel}: not UTF-8") from exc


def module_path(tree, name: str):
    base = SIDECAR + "/" + name.replace(".", "/")
    if tree.exists(base + ".py"):
        return base + ".py"
    if tree.exists(base + "/__init__.py"):
        return base + "/__init__.py"
    return None


def module_source_digest(tree, name: str) -> str:
    """input_vector._module_source_digest: sha256 of the source text; dasha_read also binds its reviewed settlement."""
    path = module_path(tree, name)
    if path is None:
        raise EqrRefusal(f"module {name}: no file in the tree")
    source = _text(tree, path)
    if name == "services.gochara_kernel.dasha_read":
        source += "\0" + _text(tree, path.rsplit("/", 1)[0] + "/dasha_settlement.json")
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


# ── a restricted constant evaluator (module-level literals; anything else is Unreadable, never guessed) ───────────────────────────────────

class ConstEnv:
    def __init__(self, source: str, label: str):
        try:
            module = ast.parse(source)
        except SyntaxError as exc:
            raise EqrRefusal(f"{label}: not parsable ({exc.msg})") from exc
        self.label, self.nodes, self._done, self._busy = label, {}, {}, set()
        for n in module.body:
            if isinstance(n, ast.Assign):
                for t in n.targets:
                    if isinstance(t, ast.Name):
                        self.nodes[t.id] = n.value
                    elif isinstance(t, ast.Tuple) and isinstance(n.value, ast.Tuple) and len(t.elts) == len(n.value.elts) \
                            and all(isinstance(e, ast.Name) for e in t.elts):
                        for e, v in zip(t.elts, n.value.elts):
                            self.nodes[e.id] = v
            elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.value is not None:
                self.nodes[n.target.id] = n.value

    def has(self, name: str) -> bool:
        return name in self.nodes

    def get(self, name: str):
        if name in self._done:
            return self._done[name]
        if name not in self.nodes:
            raise Unreadable(f"{self.label}: no module-level constant {name}")
        if name in self._busy:
            raise Unreadable(f"{self.label}: {name} is defined in terms of itself")
        self._busy.add(name)
        try:
            self._done[name] = self._ev(self.nodes[name], {})
        finally:
            self._busy.discard(name)
        return self._done[name]

    def _ev(self, n, scope):
        if isinstance(n, ast.Constant):
            v = n.value
            if isinstance(v, float):
                return repr(v)                      # a REAL is its decimal text
            if v is None or isinstance(v, (str, int, bool)):
                return v
        elif isinstance(n, ast.JoinedStr):
            return "".join(self._ev(p, scope) if isinstance(p, ast.Constant) else self._fmt(p, scope) for p in n.values)
        elif isinstance(n, ast.Name):
            return scope[n.id] if n.id in scope else self.get(n.id)
        elif isinstance(n, (ast.Tuple, ast.List)):
            return [self._ev(e, scope) for e in n.elts]
        elif isinstance(n, ast.Set):
            return sorted((self._ev(e, scope) for e in n.elts), key=canonical_json)
        elif isinstance(n, ast.Dict) and all(k is not None for k in n.keys):
            return {self._ev(k, scope): self._ev(v, scope) for k, v in zip(n.keys, n.values)}
        elif isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Mult)):
            a, b = self._ev(n.left, scope), self._ev(n.right, scope)
            if type(a) is type(b) and isinstance(a, (str, list)) and isinstance(n.op, ast.Add):
                return a + b
            if isinstance(a, int) and isinstance(b, int) and not isinstance(a, bool) and not isinstance(b, bool):
                return a + b if isinstance(n.op, ast.Add) else a * b
        elif isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            v = self._ev(n.operand, scope)
            if isinstance(v, int) and not isinstance(v, bool):
                return -v
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("tuple", "list", "frozenset", "set", "sorted") \
                and len(n.args) == 1 and not n.keywords:
            seq = self._comp(n.args[0], scope) if isinstance(n.args[0], (ast.GeneratorExp, ast.ListComp)) else self._ev(n.args[0], scope)
            if isinstance(seq, list):
                return sorted(seq, key=canonical_json) if n.func.id in ("frozenset", "set", "sorted") else seq
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "join" and isinstance(n.func.value, ast.Constant) \
                and isinstance(n.func.value.value, str) and len(n.args) == 1 and not n.keywords:
            # `"<literal>".join(<constant list of str>)` - result_policy.QUALIFICATION_TABLE builds rule 2's text this way (SOLVER_BLANK_REASONS)
            seq = self._ev(n.args[0], scope)
            if isinstance(seq, list) and all(isinstance(e, str) for e in seq):
                return n.func.value.value.join(seq)
        raise Unreadable(f"{self.label}: line {getattr(n, 'lineno', '?')}: a {type(n).__name__} is outside the restricted evaluator")

    def _fmt(self, n, scope):
        if isinstance(n, ast.FormattedValue) and n.conversion == -1 and n.format_spec is None:
            v = self._ev(n.value, scope)
            if isinstance(v, (str, int)) and not isinstance(v, bool):
                return str(v)
        raise Unreadable(f"{self.label}: an f-string part is outside the restricted evaluator")

    def _comp(self, n, scope):
        if len(n.generators) != 1 or n.generators[0].ifs or not isinstance(n.generators[0].target, ast.Name):
            raise Unreadable(f"{self.label}: a comprehension shape outside the restricted evaluator")
        g = n.generators[0]
        return [self._ev(n.elt, {**scope, g.target.id: item}) for item in self._ev(g.iter, scope)]


class _Consts:
    """ConstEnv per file of ONE tree (parsed once)."""

    def __init__(self, tree):
        self.tree, self._envs = tree, {}

    def env(self, rel: str) -> ConstEnv:
        if rel not in self._envs:
            self._envs[rel] = ConstEnv(_text(self.tree, rel), rel)
        return self._envs[rel]

    def get(self, rel: str, name: str):
        return self.env(rel).get(name)


# ── E1: the static import closure (a port of tests/l3/gochara/_import_closure.py onto the commit's bytes) ──────────────────────────────────

def _imports(tree, name: str) -> set:
    path = module_path(tree, name)
    if path is None or not path.endswith(".py"):
        return set()
    pkg = name if path.endswith("/__init__.py") else name.rsplit(".", 1)[0]
    out: set = set()
    for n in ast.walk(ast.parse(_text(tree, path))):
        if isinstance(n, ast.Import):
            out.update(a.name for a in n.names)
        elif isinstance(n, ast.ImportFrom):
            if n.level:
                base = pkg.split(".")
                base = base[: len(base) - (n.level - 1)]
                m = ".".join(base + ([n.module] if n.module else []))
            else:
                m = n.module or ""
            out.add(m)
            out.update(f"{m}.{a.name}" for a in n.names)
    return out


def writer_closure(tree, root: str = WRITER_MODULE) -> set:
    seen: set = set()
    stack = [root]
    while stack:
        m = stack.pop()
        if m in seen:
            continue
        seen.add(m)
        for i in _imports(tree, m):
            if (i.startswith(CLOSURE_ROOTS) or i == root) and module_path(tree, i) is not None and module_path(tree, i).endswith(".py") \
                    and i not in seen:
                stack.append(i)
    return {m for m in seen if m.startswith(CLOSURE_ROOTS) and not m.endswith(".__init__")} - set(CLOSURE_ROOTS)


def _qualification_check_bodies(tree) -> dict:
    pat = re.compile(r"CREATE\s+OR\s+REPLACE\s+FUNCTION\s+public\." + QUALIFICATION_CHECK_FUNCTION + r"\s*\(.*?\$\$\s*;", re.S | re.I)
    out = {}
    files = tree.list_files(MIGRATIONS)
    if hasattr(tree, "prefetch"):
        tree.prefetch(files)
    for rel in files:
        base = rel[len(MIGRATIONS):]
        m = re.match(r"(\d+)_.*\.sql$", base)
        if not m or int(m.group(1)) < QUALIFICATION_CHECK_FIRST_MIGRATION:
            continue
        for i, hit in enumerate(pat.findall(_text(tree, rel))):
            out[f"{base}#{i}"] = hashlib.sha256(hit.encode("utf-8")).hexdigest()
    return out


def build_e1(tree, consts, vec):
    """-> (subtree, e1 module names). Raises EqrRefusal for an uncovered closure module, a required module in no list, a missing listed
    module or a pinned vector that is not of this commit."""
    lists = consts.get(INPUT_VECTOR_REL, "IMPLEMENTATION_MODULES")
    if not isinstance(lists, dict) or not lists or any(not isinstance(v, list) or not all(isinstance(x, str) for x in v) for v in lists.values()):
        raise EqrRefusal(f"{INPUT_VECTOR_REL}: IMPLEMENTATION_MODULES is not {{stage: [module, ...]}}")
    listed = {m for v in lists.values() for m in v}
    shas = {m: module_source_digest(tree, m) for m in sorted(listed)}
    closure = writer_closure(tree)
    if closure - listed:
        raise EqrRefusal("modules in the writer's import closure but in no IMPLEMENTATION_MODULES list (editing one would not move the vector): "
                         + ", ".join(sorted(closure - listed)))
    required = {}
    for m in REQUIRED_RESULT_BEARING:
        if module_path(tree, m) is None:
            required[m] = "absent"
        elif m in listed:
            required[m] = "listed"
        else:
            raise EqrRefusal(f"{m} exists in the tree but is in no IMPLEMENTATION_MODULES list (editing it would not change E1)")
    stage_digest = {st: sha({m: shas[m] for m in names}) for st, names in sorted(lists.items())}
    if vec["implementation"] != stage_digest:
        raise EqrRefusal("the pinned input vector's `implementation` stage digests are not the ones this commit's bytes give — the pinned inputs "
                         f"are not of this commit (vector {sorted(vec['implementation'])}, commit {sorted(stage_digest)})")
    resources = {"qualification_check": _qualification_check_bodies(tree)}
    if "services.gochara_kernel.dasha_read" in listed:
        resources["dasha_settlement"] = sha_bytes(_text(tree, KERNEL + "/dasha_settlement.json").encode("utf-8"))
    return {"modules": shas, "stage_lists": {st: list(v) for st, v in sorted(lists.items())}, "closure": sorted(closure),
            "required_modules": required, "resources": resources}, set(listed)


# ── E2..E5 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def _need(d, *path):
    cur = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur or cur[k] in (None, {}, []):
            raise Unreadable("pinned inputs: " + ".".join(path) + " is absent")
        cur = cur[k]
    return cur


def build_e2(consts, pinned, vec):
    sel = _need(pinned, "rules", "selection")
    if sorted(sel) != ["profile", "selected_rule_version"]:
        raise Unreadable("pinned inputs: rules.selection keys must be exactly profile, selected_rule_version")
    q = consts.env(RESULT_POLICY_REL)
    return {
        "registry": vec["registry"],
        "selection": {**sel, "near_miss_layer_version": vec.get("near_miss_layer_version", "absent")},
        "rulings": vec["rulings_digest"],
        "qualification": {"table": q.get("QUALIFICATION_TABLE"), "policies": q.get("RESULT_POLICIES"),
                          "vector_result_policy": vec["result_policy"], "vector_table": vec.get("qualification_table", "absent")},
        "convention": {"kala": consts.get(RECORD_STORE_REL, "KALA_CONVENTION_VECTOR"), "sky_convention": vec["sky_convention"], "node": vec["node"]},
        "orb_policy": {"admission_digest": vec["orb_policy"]["admission_digest"], "activity": vec["orb_policy"]["activity"],
                       "orb_table": consts.get(CONVENTION_REL, "ORB_TABLE"), "point_orb_source": consts.get(RECORD_STORE_REL, "POINT_ORB_SOURCE")},
        "declared_accuracy": _need(pinned, "rules", "declared_accuracy"),
    }


def _row_digests(rows) -> dict:
    return {k: sha(v) for k, v in sorted(rows.items())}


def build_e3(pinned, vec):
    """-> (E3a subtree, flat {row_key: content sha} of the E3a rows, E3b {row_key: content sha} or None)."""
    e3a = _need(pinned, "inputs", "e3a")
    if sorted(e3a) != ["av_declarations", "dasha", "l0_rows", "l1_facts"]:
        raise Unreadable("pinned inputs: inputs.e3a keys must be exactly av_declarations, dasha, l0_rows, l1_facts")
    dasha = e3a["dasha"]
    if not isinstance(dasha, dict) or sorted(dasha) != ["held_state", "population"]:
        raise Unreadable("pinned inputs: inputs.e3a.dasha keys must be exactly held_state, population")
    l0 = {a: _row_digests(r) for a, r in sorted(e3a["l0_rows"].items())}
    sub = {"l0": {"loader_digests": vec["l0"], "rows": l0}, "l1": _row_digests(e3a["l1_facts"]),
           "dasha": {"population": _row_digests(dasha["population"]), "held_state": sha(dasha["held_state"])},
           "av": _row_digests(e3a["av_declarations"])}
    flat = e3_row_keys(sub)
    pop = pinned.get("inputs", {}).get("e3b_population")
    return sub, flat, (None if pop is None else {k: sha(v) for k, v in sorted(pop.items())})


def e3_row_keys(sub: dict) -> dict:
    flat = {}
    for a, rows in sub["l0"]["rows"].items():
        flat.update({f"l0:{a}:{i}": d for i, d in rows.items()})
    flat.update({f"l1:{i}": d for i, d in sub["l1"].items()})
    flat.update({f"dasha:population:{i}": d for i, d in sub["dasha"]["population"].items()})
    flat["dasha:held_state"] = sub["dasha"]["held_state"]
    flat.update({f"av:{i}": d for i, d in sub["av"].items()})
    return flat


def check_emulation_note(pinned, rt):
    """SR-T24-AMD64-DOCKER.  A qualifying run that carries `emulated` or `arch_probe` is a container run: (1) `emulated` must be a bool; (2) the arch was READ inside the container —
    `arch_probe` {source: in_container, uname_machine: x86_64, sys_platform: linux} must agree with `arch` (an arch asserted from outside is refused); (3) when emulated, the emulation is
    recorded in `provenance.platform_notes.emulation` {emulated: true, layer}.  The note is E6 (never compared), so it can never make a record DIFFER."""
    if rt.get("kind") != "qualifying_run" or ("emulated" not in rt and "arch_probe" not in rt):
        return
    if not isinstance(rt.get("emulated"), bool):
        raise EqrRefusal("runtime.emulated must be true or false for a container run")
    probe = rt.get("arch_probe")
    if (not isinstance(probe, dict) or probe.get("source") != "in_container" or probe.get("uname_machine") != "x86_64"
            or probe.get("sys_platform") != "linux" or rt.get("arch") != QUALIFYING_ARCH):
        raise EqrRefusal("runtime.arch must be read inside the container (arch_probe: source in_container, uname_machine x86_64, sys_platform linux): an architecture asserted from outside is refused")
    if rt["emulated"]:
        note = (pinned.get("provenance") or {}).get("platform_notes", {}).get("emulation")
        if not isinstance(note, dict) or note.get("emulated") is not True or note.get("layer") not in EMULATION_LAYERS:
            raise EqrRefusal(f"an emulated run records the emulation in provenance.platform_notes.emulation {{emulated: true, layer: {'|'.join(EMULATION_LAYERS)}}}")


def build_e4(tree, pinned, vec):
    rt = _need(pinned, "runtime")
    kind = rt.get("kind")
    if kind not in RUNTIME_KINDS:
        raise EqrRefusal(f"runtime.kind {kind!r} is not one of {RUNTIME_KINDS}")
    if kind == "rolling_diagnostic":
        raise Unreadable("a rolling diagnostic run has no E4 (P3/P6: only the qualifying amd64 run and the dispatch image are compared)")
    if kind == "qualifying_run" and rt.get("arch") != QUALIFYING_ARCH:
        raise Unreadable(f"the qualifying run must be {QUALIFYING_ARCH} (arm64 runs are corroboration), not {rt.get('arch')!r}")
    for k in ("arch", "python", "dependency_lock_digest"):
        _need(rt, k)
    check_emulation_note(pinned, rt)
    eph = vec["ephemeris"]
    return {"swiss": {"backend": eph["backend"], "swe_version": eph["swe_version"], "library_sha256": eph["library_sha256"], "files": eph["files"]},
            "probe": eph["probe_digest"], "platform": {"vector": eph["platform"], "arch": rt["arch"]}, "python": rt["python"],
            "dependency_lock": {"requirements_sha256": sha_bytes(_text(tree, REQUIREMENTS_REL).encode("utf-8")),
                                "installed_lock_digest": rt["dependency_lock_digest"]}}


def resolve_tolerances(consts, modules) -> dict:
    out = {}
    for tol, names in TOLERANCES.items():
        hits = {}
        for mod in sorted(modules):
            path = module_path(consts.tree, mod)
            if path is None or not path.endswith(".py"):
                continue
            env = consts.env(path)
            for n in names:
                if env.has(n):
                    hits[f"{mod}:{n}"] = env.get(n)
        if not hits:
            raise Unreadable(f"tolerance {tol} is declared by no module constant ({', '.join(names)}) in the E1 module set")
        if len({canonical_json(v) for v in hits.values()}) > 1:
            raise Unreadable(f"tolerance {tol} is declared with different values: {sorted(hits)}")
        out[tol] = {"value": next(iter(hits.values())), "declared_in": sorted(hits)}
    return out


def build_e5(consts, modules, pinned):
    cc = _need(pinned, "century_config")
    leaked = [k for k in cc if k in TRIAL_SCOPE_KEYS]
    if leaked:
        raise EqrRefusal(f"century_config carries trial-scope field(s) {leaked}: the manifest would be unsealable by construction (P1)")
    if sorted(cc) != sorted(CENTURY_KEYS):
        raise EqrRefusal(f"century_config keys {sorted(cc)} != {sorted(CENTURY_KEYS)}")
    if cc["stored_scope"] != CENTURY_STORED_SCOPE:
        raise EqrRefusal(f"century_config.stored_scope {cc['stored_scope']!r} != {CENTURY_STORED_SCOPE!r} (a trial scope in a century config, P1)")
    classes = cc["classes"]
    if not isinstance(classes, list) or not classes or len(set(classes)) != len(classes) or not all(isinstance(c, str) for c in classes):
        raise EqrRefusal("century_config.classes must be a non-empty list of distinct names")
    return {"century": {k: cc[k] for k in ("stored_scope", "horizon", "horizon_basis", "final_rules", "result_policy", "in_build_verify")},
            "budgets": cc["budgets"], "class_universe": sorted(classes), "verification_plan": cc["verification_plan"],
            "tolerances": resolve_tolerances(consts, modules)}


# ── the record ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def validate_vector(vec):
    if not isinstance(vec, dict):
        raise EqrRefusal("pinned input_vector is not an object")
    if vec.get("schema") != VECTOR_SCHEMA:
        raise EqrRefusal(f"input_vector.schema {vec.get('schema')!r} != {VECTOR_SCHEMA!r}")
    missing = [k for k in VECTOR_REQUIRED if k not in vec]
    extra = [k for k in vec if k not in VECTOR_REQUIRED + VECTOR_OPTIONAL]
    if missing or extra:
        raise EqrRefusal(f"input_vector keys: missing {missing}, unknown {extra}")
    if sorted(vec["ephemeris"]) != sorted(EPHEMERIS_KEYS):
        raise EqrRefusal(f"input_vector.ephemeris keys {sorted(vec['ephemeris'])} != {sorted(EPHEMERIS_KEYS)}")
    if sorted(vec["orb_policy"]) != ["activity", "admission_digest"]:
        raise EqrRefusal("input_vector.orb_policy keys must be exactly activity, admission_digest")


def load_pinned(path) -> dict:
    pinned = loads(Path(path).read_bytes(), str(path))
    if not isinstance(pinned, dict) or pinned.get("schema") != PINNED_SCHEMA:
        raise EqrRefusal(f"{path}: schema is not {PINNED_SCHEMA}")
    extra = [k for k in pinned if k not in PINNED_KEYS]
    if extra:
        raise EqrRefusal(f"{path}: unknown pinned-input key(s) {extra}")
    if "input_vector" not in pinned:
        raise EqrRefusal(f"{path}: input_vector is required")
    validate_vector(pinned["input_vector"])
    prov = pinned.get("provenance", {})
    if not isinstance(prov, dict) or [k for k in prov if k not in PROVENANCE_KEYS]:
        raise EqrRefusal(f"{path}: provenance keys must be among {PROVENANCE_KEYS}")
    return pinned


def _parts(subtree: dict) -> dict:
    out = {}
    for k, v in subtree.items():
        if k == "modules":
            out.update({f"modules.{m}": d for m, d in v.items()})
        else:
            out[k] = sha(v)
    return out


def _category(subtree, reasons):
    if reasons or subtree is None:
        return {"digest": None, "parts": _parts(subtree) if subtree else {}, "unreadable": sorted(reasons), "manifest": None}, None
    body = canonical_json(subtree).encode("utf-8")
    d = sha_bytes(body)
    return {"digest": d, "parts": _parts(subtree), "unreadable": [], "manifest": {"name": None, "sha256": d, "bytes": len(body)}}, body


def build_record(tree, pinned: dict, generated_at: str):
    """-> (record document, {manifest file name: bytes}). EqrRefusal when a category cannot be built honestly at all."""
    vec = pinned["input_vector"]
    consts = _Consts(tree)
    subtrees, reasons, manifests = {}, {c: [] for c in CATEGORIES}, {}
    e1, modules = build_e1(tree, consts, vec)
    subtrees["E1"] = e1
    for cat, fn in (("E2", lambda: build_e2(consts, pinned, vec)), ("E4", lambda: build_e4(tree, pinned, vec)),
                    ("E5", lambda: build_e5(consts, modules, pinned))):
        try:
            subtrees[cat] = fn()
        except Unreadable as exc:
            subtrees[cat] = None
            reasons[cat].append(str(exc))
    e3b = None
    try:
        subtrees["E3"], flat, e3b = build_e3(pinned, vec)
    except Unreadable as exc:
        subtrees["E3"], flat = None, {}
        reasons["E3"].append(str(exc))
    cats = {}
    for c in CATEGORIES:
        cats[c], body = _category(subtrees[c], reasons[c])
        if body is not None:
            cats[c]["manifest"]["name"] = f"{c}.json"
            manifests[f"{c}.json"] = body
    if e3b is not None:
        body = canonical_json(e3b).encode("utf-8")
        cats["E3"]["e3b"] = {"row_count": len(e3b), "population_sha256": sha_bytes(body), "manifest": {"name": "E3b.json", "sha256": sha_bytes(body)}}
        manifests["E3b.json"] = body
    else:
        cats["E3"]["e3b"] = None
    digests = [cats[c]["digest"] for c in CATEGORIES]
    complete = all(d is not None for d in digests)
    trial_scope_values = {"trial.stored_scope": vec["stored_scope"], "trial.test_slice": vec.get("test_slice"),
                          "trial.horizon_basis": vec.get("horizon_basis"), "trial.class_subset": vec.get("scored_classes"),
                          "trial.horizon": pinned.get("trial_scope", {}).get("horizon")}
    century_classes = pinned.get("century_config", {}).get("classes") or []
    subset = vec.get("scored_classes") or []
    record = {
        "schema": SCHEMA, "complete": complete, "record_digest": sha(digests) if complete else None, "categories": cats,
        "projection": {"excluded_fields": list(PROJECTION_EXCLUDED),
                       "excluded_values_sha256": {k: (None if v is None else sha(v)) for k, v in sorted(trial_scope_values.items())},
                       "no_trial_evidence_classes": sorted(set(century_classes) - set(subset)) if subset else None},
        "runtime_kind": pinned.get("runtime", {}).get("kind"),
        "E6": {"commit": tree.commit, "tree": tree.tree, "generated_at": generated_at, "tool": SCHEMA,
               **{k: v for k, v in sorted(pinned.get("provenance", {}).items())}},
    }
    return record, manifests


def record_bytes(record: dict) -> bytes:
    return canonical_json(record).encode("utf-8")


def write_record(record: dict, manifests: dict, out) -> Path:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    mdir = out.with_name(out.name + ".manifests")
    mdir.mkdir(parents=True, exist_ok=True)
    for name, body in manifests.items():
        (mdir / name).write_bytes(body)
    out.write_bytes(record_bytes(record))
    return out


# ── loading a record (the detectors of the comparison side) ──────────────────────────────────────────────────────────────────────────────

class LoadedRecord:
    def __init__(self, path, doc, raw, manifests):
        self.path, self.doc, self.sha, self._manifests = Path(path), doc, sha_bytes(raw), manifests

    def manifest(self, name):
        return self._manifests.get(name)


def load_record(path) -> LoadedRecord:
    path = Path(path)
    raw = path.read_bytes()
    doc = loads(raw, str(path))
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA:
        raise EqrRefusal(f"{path}: not an {SCHEMA} document")
    if raw != record_bytes(doc):
        raise EqrRefusal(f"{path}: not in canonical form (sorted keys, no insignificant whitespace)")
    cats = doc.get("categories")
    if not isinstance(cats, dict) or sorted(cats) != sorted(CATEGORIES):
        raise EqrRefusal(f"{path}: categories must be exactly {CATEGORIES}")
    digests = [cats[c].get("digest") for c in CATEGORIES]
    want = sha(digests) if all(d is not None for d in digests) else None
    if doc.get("record_digest") != want or doc.get("complete") is not (want is not None):
        raise EqrRefusal(f"{path}: record_digest/complete do not follow from the five category digests")
    if doc.get("projection", {}).get("excluded_fields") != list(PROJECTION_EXCLUDED):
        raise EqrRefusal(f"{path}: projection.excluded_fields is not the fixed list {list(PROJECTION_EXCLUDED)} — nothing else may be excluded (P1)")
    mdir = path.with_name(path.name + ".manifests")
    manifests = {}
    for c in CATEGORIES:
        entries = [("E3b.json", cats[c].get("e3b", None) and cats[c]["e3b"]["manifest"])] if c == "E3" else []
        entries.append((f"{c}.json", cats[c].get("manifest")))
        for name, entry in entries:
            if not entry:
                continue
            f = mdir / name
            if f.is_file():
                body = f.read_bytes()
                if sha_bytes(body) != entry["sha256"]:
                    raise EqrRefusal(f"{f}: manifest bytes do not match the record's index (sha256)")
                manifests[name] = loads(body, str(f))
    return LoadedRecord(path, doc, raw, manifests)


# ── the decision (§3.4) and the re-qualification table (§3.5, DATA) ─────────────────────────────────────────────────────────────────────

def load_table(path=TABLE_PATH) -> dict:
    t = loads(Path(path).read_bytes(), str(path))
    if t.get("schema") != TABLE_SCHEMA:
        raise EqrRefusal(f"{path}: schema is not {TABLE_SCHEMA}")
    rank = t["action_rank"]
    for row in t["rows"]:
        if row["action"] not in rank:
            raise EqrRefusal(f"{path}: row {row['id']} names action {row['action']!r} that has no rank")
    return t


def _rows(table) -> dict:
    return {r["id"]: r for r in table["rows"]}


def _differing_parts(a: dict, b: dict) -> list:
    return sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))


def _classify(cat, parts, table) -> list:
    """The table-row ids that apply to a category whose digests differ, from the differing parts."""
    if cat == "E1":
        inside = set(table["e1_solver_checker_evaluator_modules"])
        non_module = [p for p in parts if not p.startswith("modules.")]
        return ["E1.inside"] if non_module or any(p[len("modules."):] in inside for p in parts if p.startswith("modules.")) else ["E1.outside"]
    if cat == "E2":
        return ["E2"]
    if cat == "E3":
        return ["E3a.l0"] if "l0" in parts else ["E3a.other"]
    if cat == "E4":
        return ["E4.probe"] if "probe" in parts else ["E4.other"]
    return ["E5.budgets_or_tolerances"] if {"budgets", "tolerances"} & set(parts) else ["E5.other"]


def e3b_coverage(trial: LoadedRecord, main: LoadedRecord):
    """P2: every trial E3a row id is present in main's E3b population with identical content. -> (state, detail)."""
    e3a = trial.manifest("E3.json")
    e3b = main.manifest("E3b.json")
    if e3a is None or e3b is None:
        return "unreadable", ["the trial E3 manifest or main's E3b population manifest is not available (or main bound no E3b)"]
    bad = sorted(k for k, d in e3_row_keys(e3a).items() if e3b.get(k) != d)
    return ("ok", []) if not bad else ("missing_rows", bad)


def decide(trial: LoadedRecord, main: LoadedRecord, table: dict) -> dict:
    rows = _rows(table)
    per, applied, unreadable = {}, [], {}
    for c in CATEGORIES:
        ta, ma = trial.doc["categories"][c], main.doc["categories"][c]
        if ta["digest"] is None or ma["digest"] is None:
            per[c] = "differs"
            unreadable[c] = {"trial": ta["unreadable"], "main": ma["unreadable"]}
            applied.append("UNREADABLE")
        elif ta["digest"] == ma["digest"]:
            per[c] = "equal"
        else:
            per[c] = "differs"
            applied += _classify(c, _differing_parts(ta["parts"], ma["parts"]), table)
    cov, cov_detail = e3b_coverage(trial, main)
    if cov != "ok":
        applied.append("E3b.coverage")
    equal = all(v == "equal" for v in per.values()) and cov == "ok"
    if equal:
        applied = ["E6.only"]
    rank = table["action_rank"]
    chosen = [rows[i] for i in dict.fromkeys(applied)]
    overall = max((r["action"] for r in chosen), key=lambda a: rank[a])
    return {
        "schema": DECISION_SCHEMA, "trial_record_sha": trial.sha, "main_record_sha": main.sha,
        "trial_record_digest": trial.doc["record_digest"], "main_record_digest": main.doc["record_digest"],
        "per_category": {**per, "E3b_coverage": cov, "E6": "stored_not_compared"},
        "decision": "EQUAL" if equal else "DIFFERS",
        "action": {"overall": overall, "rows": [{"id": r["id"], "action": r["action"], "text": r["text"]} for r in chosen],
                   "flags": sorted({f for r in chosen for f in r.get("flags", [])})},
        "detail": {"differing_parts": {c: _differing_parts(trial.doc["categories"][c]["parts"], main.doc["categories"][c]["parts"])
                                       for c in CATEGORIES if per[c] == "differs" and c not in unreadable},
                   "unreadable": unreadable, "e3b_coverage_rows": cov_detail},
        "provenance": {"trial": trial.doc["E6"], "main": main.doc["E6"]},
        "manifests_verified": {c: all(n in trial._manifests and n in main._manifests for n in (f"{c}.json",)) for c in CATEGORIES},
    }


# ── CLI ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record")
    r.add_argument("--repo", required=True)
    r.add_argument("--commit", required=True)
    r.add_argument("--pinned-inputs", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--generated-at", default=None)
    c = sub.add_parser("compare")
    c.add_argument("--trial", required=True)
    c.add_argument("--main", required=True)
    c.add_argument("--out", default=None)
    c.add_argument("--table", default=str(TABLE_PATH))
    a = ap.parse_args(argv)
    try:
        if a.cmd == "record":
            rec, mans = build_record(GitTree(a.repo, a.commit), load_pinned(a.pinned_inputs), a.generated_at or _now())
            write_record(rec, mans, a.out)
            print(json.dumps({"out": a.out, "complete": rec["complete"], "record_digest": rec["record_digest"],
                              "unreadable": {k: v["unreadable"] for k, v in rec["categories"].items() if v["unreadable"]}}, sort_keys=True))
            return 0 if rec["complete"] else 2
        decision = decide(load_record(a.trial), load_record(a.main), load_table(a.table))
        text = canonical_json(decision)
        if a.out:
            Path(a.out).parent.mkdir(parents=True, exist_ok=True)
            Path(a.out).write_text(text, encoding="utf-8")
        print(text)
        return 0 if decision["decision"] == "EQUAL" else 3
    except EqrRefusal as exc:
        print(f"equivalence_record: REFUSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
