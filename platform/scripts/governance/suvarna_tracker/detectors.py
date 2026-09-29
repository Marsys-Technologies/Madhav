"""Detectors — the checks that decide whether a plan item is really done.

Earned-signal rule (CLAUDE.md §N.8): wherever a fact can be checked, a detector decides the
status; no typed number does. Each detector:
- runs in a worker thread with its own timeout, so a slow or failing one never freezes the view;
- is cached for its own TTL (git 5 min, GitHub 2 min, files 20 s, database 1 min);
- returns a DetectorResult that always says when it was checked and what it saw;
- reports `error` (never `done`) when it cannot measure — an unmeasured check is not a pass.
"""
from __future__ import annotations

import collections
import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass

from .events import now_iso

PIPE_SPLIT = re.compile(r"(?<!\\)\|")
STATE_CLASSES = ("CLOSED_ON_BRANCH", "OPEN", "CLOSED", "DONE", "PARTIAL", "MEASURED",
                 "DEFERRED", "WITHDRAWN", "IN_PROGRESS")


@dataclass
class DetectorResult:
    status: str            # done | running | pending | blocked | error
    detail: str
    checked_at: str
    source: str
    progress: float | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Config:
    repo: str              # a checkout of the project repo (for git/gh)
    nikasha_root: str      # checkout holding the register and ledgers (campaign/nikasha-test until landed)
    pgenv: str | None      # path to the read-only DB env file (sourced by bash), or None
    home: str              # SUVARNA_HOME
    db_port: int = 5433


def _run(cmd: list[str] | str, cwd: str | None = None, timeout: int = 60, shell: bool = False,
         env: dict | None = None) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=cwd, timeout=timeout, shell=shell, capture_output=True, text=True, env=env)
    return p.returncode, (p.stdout if p.returncode == 0 else (p.stderr or p.stdout))


# --------------------------------------------------------------------------------------------
# Committed-ref reads (Fix 5, review #17): the register and ledgers must reflect what's actually
# on the branch's last commit, never an in-flight working-tree edit — a detector measuring a
# working copy could show "closed" for a change that was never committed. `NIKASHA_REF` (default
# HEAD) selects the ref; a failed `git show` is surfaced as an error, never silently falls back to
# the working tree.
# --------------------------------------------------------------------------------------------

REGISTER_REL_PATH = "00_ARCHITECTURE/briefs/nirmana/NIKASHA_CHANGE_REGISTER_v2_0.md"
GAPS_REL_PATH = "00_ARCHITECTURE/control/asset_gaps.jsonl"
CERTS_REL_PATH = "00_ARCHITECTURE/control/asset_certs.jsonl"

# v1.3 additions (arch §11.7, built by L.13). Two of the new detector types read committed inputs
# that other L.13-dependent work (E6.3, E6.1/E6.5) has not landed yet: FAMILY_ASSETS.json (on
# `origin/main`, alongside the rest of the tracker's own config) and the inspector's registry
# self-check report (in the Nikaṣa root, alongside the register and ledgers it is measured
# against). Until each lands, its detector(s) correctly read `pending` — "an expected input that
# does not exist yet reads pending" (arch §11.7 rule).
#
# Review pass 2 (consistency #7): the tracker's own hardcoded path disagreed with the plan model
# and Track E brief's `00_ARCHITECTURE/control/FAMILY_ASSETS.json` (no `suvarna/` subdirectory),
# so the wave/family detectors would never see the file once E6.3 actually landed it. The path is
# now one configurable setting, `SUVARNA_FAMILY_ASSETS_PATH`, defaulting to the plan model/Track E
# path — never a second hardcoded copy that can drift from it again.
DEFAULT_FAMILY_ASSETS_REL_PATH = "00_ARCHITECTURE/control/FAMILY_ASSETS.json"
REGISTRY_COVERAGE_REL_PATH = "00_ARCHITECTURE/control/registry_coverage_report.json"

# Review pass 2 (consistency #6, substance): `NIKASHA_WITHHOLDING.json` (E5.2 fold script; ROLE_SCRIBE
# §"current withholding list") — the committed record of which register rows are DEFERRED with a
# withholding actually in force, read at the pinned Nikaṣa ref, same discipline as the register.
DEFAULT_WITHHOLDING_REL_PATH = "00_ARCHITECTURE/control/NIKASHA_WITHHOLDING.json"

PARAMS_NOT_SET = "detector parameters not set yet"


def _family_assets_rel_path() -> str:
    """`SUVARNA_FAMILY_ASSETS_PATH` overrides the default path (review #7) — a single configurable
    constant instead of a second hardcoded copy that can drift from the plan model/Track E brief."""
    return os.environ.get("SUVARNA_FAMILY_ASSETS_PATH") or DEFAULT_FAMILY_ASSETS_REL_PATH


# Review pass 2 (consistency #6): the tracker called a bare `suvarna-build`, a PATH lookup that
# fails since `run_tracker.sh` never adds `~/.config/suvarna/bin` to PATH, and passed a `--json`
# flag no document specifies. `SUVARNA_BUILD_CMD` pins the full path (never a bare-name lookup);
# the default matches every document that names it (ROLE_BUILD_OPERATOR, runbook, charter):
# `~/.config/suvarna/bin/suvarna-build`, mode 700, provisioned by the native at E7.2.
DEFAULT_SUVARNA_BUILD_CMD = os.path.expanduser("~/.config/suvarna/bin/suvarna-build")


def _suvarna_build_cmd() -> str:
    return os.environ.get("SUVARNA_BUILD_CMD") or DEFAULT_SUVARNA_BUILD_CMD


# The build engine's own contract (Track E brief §1 E3.7, §5 E5.3, §8 E7): `suvarna-build
# --preflight` prints `{job_image_tag, deployed_sha}` — no `--json` flag anywhere the brief names
# it, and the serving key is `deployed_sha`, never `web_sha` (review #6).
_TRAILING_SHA_RE = re.compile(r"([0-9a-f]{7,40})$")


def _extract_trailing_sha(value: str) -> str | None:
    """The commit SHA a job image tag is required to end with (charter §6 precondition 4: "a writer
    change needs `job_image_tag` to end with the merged commit's SHA"). `None` when the tag's tail
    is not hex — the caller reports that as `error`, never guesses a SHA out of an arbitrary tag."""
    m = _TRAILING_SHA_RE.search((value or "").strip())
    return m.group(1) if m else None


def _nikasha_ref() -> str:
    return os.environ.get("NIKASHA_REF", "HEAD")


def _git_show_text(nikasha_root: str, rel_path: str) -> str:
    ref = _nikasha_ref()
    rc, out = _run(["git", "-C", nikasha_root, "show", f"{ref}:{rel_path}"], timeout=30)
    if rc != 0:
        raise RuntimeError(f"git show {ref}:{rel_path} failed: {out.strip()[:200]}")
    return out


def register_text(nikasha_root: str) -> str:
    return _git_show_text(nikasha_root, REGISTER_REL_PATH)


# --------------------------------------------------------------------------------------------
# Register parsing (shared by several detectors and by the metrics)
# --------------------------------------------------------------------------------------------

def classify_state(cell: str) -> str:
    t = cell.strip().lstrip("*").strip().upper()
    for k in STATE_CLASSES:
        if t.startswith(k):
            return k
    return "OTHER"


def parse_register(source: str) -> dict:
    """Rows keyed by id: {'severity','state_class','state'}; plus the header tally and malformed rows.

    `source` is either a file path or the register's own text (auto-detected: a path never
    contains a newline, the register's markdown always does) — so a caller reading a committed ref
    via `git show` (Fix 5) can hand this the text directly, with no working-tree file involved.

    Header-aware: the register holds tables with different column layouts (the build-system rows
    carry two extra columns). Each row is read against the most recent table header above it, and
    the severity and state columns are located by name, never by fixed position. A row whose cell
    count differs from its table's header is flagged malformed (its named columns are still read).
    """
    text = source if "\n" in source else open(source, encoding="utf-8").read()
    rows, malformed, header = {}, [], {}
    in_tally = False
    layout = {"n": 9, "severity": 4, "state": 7}  # default: # | change | surfaced | severity | depends | effort | state
    for line in text.splitlines(keepends=True):
        if line.startswith("### 0.1"):
            in_tally = True
            continue
        if in_tally and line.startswith("###"):
            in_tally = False
        if in_tally:
            m = re.match(r"^\|\s*([A-Za-z_ 0-9]+?)\s*\|\s*(\d+)\s*\|", line)
            if m and m.group(1).lower() != "state":
                header[m.group(1).strip()] = int(m.group(2))
            continue
        if re.match(r"^\|\s*#\s*\|", line):
            names = [c.strip().lower() for c in PIPE_SPLIT.split(line.rstrip("\n"))]
            if "severity" in names and "state" in names:
                layout = {"n": len(names), "severity": names.index("severity"), "state": names.index("state")}
            continue
        m = re.match(r"^\| (R\d+) \|", line)
        if not m:
            continue
        cells = [c.strip() for c in PIPE_SPLIT.split(line.rstrip("\n"))]
        if len(cells) != layout["n"]:
            malformed.append(m.group(1))
        get = lambda i: cells[i] if i < len(cells) else ""
        state = get(layout["state"])
        rows[m.group(1)] = {"severity": get(layout["severity"]), "state_class": classify_state(state), "state": state[:200]}
    return {"rows": rows, "malformed": malformed, "header": header}


def register_counts(reg: dict) -> dict:
    by_state = collections.Counter(r["state_class"] for r in reg["rows"].values())
    open_by_sev = collections.Counter(r["severity"] for r in reg["rows"].values() if r["state_class"] == "OPEN")
    return {"total": len(reg["rows"]), "by_state": dict(by_state), "open_by_severity": dict(open_by_sev)}


# --------------------------------------------------------------------------------------------
# The detector registry
# --------------------------------------------------------------------------------------------

class Detectors:
    TTL = {"pr_merged": 120, "register_tally_consistent": 20, "register_wellformed": 20,
           "main_file_contains": 300, "main_has_file": 300, "branch_merged": 300,
           "register_rows_closed": 20, "db_columns_exist": 60, "levels_elevated": 60,
           # v1.3 additions (arch §11.7)
           "prs_merged": 120, "main_has_files": 300, "scorecard_pass": 300,
           "migrations_applied": 60, "register_rows_state": 20, "register_freeze_clean": 20,
           "monitor_check_ok": 60, "deployed_contains": 600, "wave_deployed": 600,
           "assets_elevated": 60, "registry_coverage": 300, "ledger_no_open_gap_on": 20,
           "evidence_recent": 300}

    def __init__(self, cfg: Config, on_change=None):
        self.cfg = cfg
        self.on_change = on_change or (lambda: None)
        self.results: dict[str, DetectorResult] = {}
        self._due: dict[str, float] = {}
        self._inflight: set[str] = set()
        self._lock = threading.Lock()
        self._pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="detector")
        self._last_fetch = 0.0
        self._fetch_lock = threading.Lock()

    # -- scheduling ---------------------------------------------------------------------------
    @staticmethod
    def key(spec: dict) -> str:
        return json.dumps(spec, sort_keys=True, ensure_ascii=False)

    def poll(self, specs: list[dict]) -> None:
        """Submit every detector whose TTL has expired. Never blocks."""
        now = time.time()
        for spec in specs:
            k = self.key(spec)
            with self._lock:
                if k in self._inflight or self._due.get(k, 0) > now:
                    continue
                self._inflight.add(k)
            self._pool.submit(self._run_one, k, spec)

    def _run_one(self, k: str, spec: dict) -> None:
        typ = spec.get("type", "?")
        try:
            fn = getattr(self, "d_" + typ)
            res = fn(spec)
        except subprocess.TimeoutExpired:
            res = DetectorResult("error", f"{typ}: timed out", now_iso(), f"detector:{typ}")
        except Exception as exc:  # isolation: one broken detector never takes down the others
            res = DetectorResult("error", f"{typ}: {type(exc).__name__}: {exc}"[:300], now_iso(), f"detector:{typ}")
        with self._lock:
            prev = self.results.get(k)
            self.results[k] = res
            self._inflight.discard(k)
            self._due[k] = time.time() + (self.TTL.get(typ, 60) if res.status != "error" else 30)
        if prev is None or (prev.status, prev.detail, prev.progress) != (res.status, res.detail, res.progress):
            self.on_change()

    def get(self, spec: dict) -> DetectorResult | None:
        with self._lock:
            return self.results.get(self.key(spec))

    # -- helpers ------------------------------------------------------------------------------
    def _fetch_main(self) -> None:
        with self._fetch_lock:
            if time.time() - self._last_fetch < 300:
                return
            _run(["git", "fetch", "-q", "origin", "main"], cwd=self.cfg.repo, timeout=90)
            self._last_fetch = time.time()

    def _register_text(self) -> str:
        """The register's text at the committed ref (NIKASHA_REF, default HEAD) — never the
        working tree (Fix 5). Raises RuntimeError if `git show` fails; callers let that propagate
        so the detector reports `error`, never falling back to reading the file off disk."""
        return register_text(self.cfg.nikasha_root)

    def _psql(self, sql: str, timeout: int = 60) -> list[list[str]]:
        if not self.cfg.pgenv or not os.path.exists(self.cfg.pgenv):
            raise RuntimeError("no read-only DB env file")
        cmd = f"source {self.cfg.pgenv} && psql -tAX -F'\t' -c {json.dumps(sql)}"
        rc, out = _run(["bash", "-c", cmd], timeout=timeout)
        if rc != 0:
            raise RuntimeError(out.strip()[:200])
        return [l.split("\t") for l in out.splitlines() if l.strip()]

    def _family_assets(self) -> dict | None:
        """`FAMILY_ASSETS.json` (arch §6.4/§11.7, frozen at J1/E6.3) — read from the committed
        `origin/main` ref, same discipline as the register (Fix 5): never the working tree. Returns
        None (never raises) when the file is not on main yet — that is the expected pre-E6.3 state,
        and callers turn it into `pending`, not `error`."""
        self._fetch_main()
        rc, out = _run(["git", "show", f"origin/main:{_family_assets_rel_path()}"], cwd=self.cfg.repo, timeout=30)
        if rc != 0:
            return None
        return json.loads(out)

    def _withholding_has_entry(self, path: str, entry: str) -> bool:
        """Whether `entry` appears in the withholding list JSON, read at the pinned Nikaṣa ref (Fix
        5 discipline — never the working tree). Returns `False` (never raises) when the file is
        absent or malformed: an absent withholding list is not evidence a withholding is in force
        (review pass 2, R244-deferred finding — a DEFERRED register row must not count on its own
        say-so; the withholding it claims has to be independently verified present)."""
        try:
            data = json.loads(_git_show_text(self.cfg.nikasha_root, path))
        except (RuntimeError, ValueError):
            return False
        if isinstance(data, list):
            return entry in data
        if isinstance(data, dict):
            return entry in data or entry in (data.get("entries") or data.get("withheld") or [])
        return False

    @staticmethod
    def _family_set_union(fam: dict, set_name: str | None = None) -> set[str]:
        """The named set's assets, or — for `set_name in (None, 'family_set')` — the union of every
        `family_*` list in the file (families and their readers alike), matching how `exclude:
        family_set` is used on the wave items."""
        if set_name and set_name != "family_set":
            v = fam.get(set_name) or []
            return set(v) if isinstance(v, list) else set()
        if isinstance(fam.get("family_set"), list):
            return set(fam["family_set"])
        out: set[str] = set()
        for k, v in fam.items():
            if k.startswith("family_") and isinstance(v, list):
                out.update(v)
        return out

    # -- PR pinning by head ref (review #9/consistency #9): `prs_merged` and `deployed_contains`
    # resolve a lane's head ref (branch name) to its PR via `gh pr list`, in addition to accepting
    # explicit PR numbers — so a spec can be written before a PR exists to number, per Track E §3.2.
    def _resolved_pr_numbers(self, spec: dict) -> tuple[list[int], list[str]]:
        """`spec['prs']` (explicit numbers) plus `spec['head_refs']` (branch names) resolved via
        `gh pr list --state all --head <ref> --json number,state,mergedAt` (read-only). Returns
        (numbers, unresolved_refs) — a head ref matching no PR yet is not an error (the lane may
        simply not have opened its PR yet); it comes back in `unresolved_refs` so the caller reads
        `pending`, never silently drops it and never reads `done` short of every head ref's own PR.
        Raises RuntimeError only when the `gh` call itself fails (network/auth/rate-limit)."""
        prs = list(spec.get("prs") or [])
        unresolved: list[str] = []
        for ref in spec.get("head_refs") or []:
            rc, out = _run(["gh", "pr", "list", "--state", "all", "--head", ref,
                            "--json", "number,state,mergedAt"], cwd=self.cfg.repo, timeout=60)
            if rc != 0:
                raise RuntimeError(f"gh pr list --head {ref}: {out.strip()[:160]}")
            found = json.loads(out)
            if not found:
                unresolved.append(ref)
                continue
            found.sort(key=lambda d: (d.get("state") == "MERGED", d.get("number", 0)), reverse=True)
            prs.append(found[0]["number"])
        return prs, unresolved

    # -- git ancestry (review #5/#7): "our commit is deployed" is never string equality or a
    # substring test — other workstreams deploy to `main` too, so a tag/SHA that once matched can
    # stop matching after any later, unrelated deploy even though the original commit is still very
    # much live. The only test that stays true across every later deploy is ancestry.
    def _fetch_commit(self, sha: str) -> None:
        """Best-effort fetch of a single commit object by SHA (read-only), so an ancestry check can
        run without a full clone. Never raises: if the remote refuses (some servers require
        `uploadpack.allowReachableSHA1InWant`/`allowAnySHA1InWant`) or there is no such remote, the
        caller's own existence re-check reports that failure — this is purely an attempt."""
        rc, _ = _run(["git", "cat-file", "-e", f"{sha}^{{commit}}"], cwd=self.cfg.repo, timeout=15)
        if rc == 0:
            return
        _run(["git", "fetch", "-q", "origin", sha], cwd=self.cfg.repo, timeout=60)

    def _is_ancestor(self, ancestor_sha: str, descendant_sha: str) -> bool:
        """True iff `ancestor_sha` is reachable from `descendant_sha` — `git merge-base
        --is-ancestor`, evaluated in `self.cfg.repo` after fetching either commit by SHA if it is
        not already present locally (read-only). A commit is its own ancestor, so this also covers
        the "equal to" case ROLE_BUILD_OPERATOR names for a serving deploy's `deployed_sha`. Raises
        RuntimeError if either commit still cannot be resolved after the fetch attempt — the caller
        reports `error`, never silently treats an unresolved commit as "not an ancestor"."""
        for sha in (ancestor_sha, descendant_sha):
            self._fetch_commit(sha)
            rc, _ = _run(["git", "cat-file", "-e", f"{sha}^{{commit}}"], cwd=self.cfg.repo, timeout=15)
            if rc != 0:
                raise RuntimeError(f"commit {sha[:12]} not resolvable locally (fetch attempted)")
        rc, _ = _run(["git", "merge-base", "--is-ancestor", ancestor_sha, descendant_sha],
                     cwd=self.cfg.repo, timeout=30)
        return rc == 0

    def _run_preflight(self) -> tuple[int, str]:
        """`suvarna-build --preflight` via the pinned full path (review #6 — never a bare-name PATH
        lookup, never `--json`: neither is in the Track E brief's own contract)."""
        return _run([_suvarna_build_cmd(), "--preflight"], timeout=60)

    # -- detectors ----------------------------------------------------------------------------
    def d_pr_merged(self, spec):
        rc, out = _run(["gh", "pr", "view", str(spec["pr"]), "--json", "state,mergedAt,mergeable"],
                       cwd=self.cfg.repo, timeout=60)
        if rc != 0:
            return DetectorResult("error", f"gh: {out.strip()[:160]}", now_iso(), "detector:pr_merged")
        d = json.loads(out)
        if d["state"] == "MERGED":
            return DetectorResult("done", f"PR #{spec['pr']} merged {d.get('mergedAt','')}", now_iso(), "detector:pr_merged", 1.0)
        if d["state"] == "OPEN":
            return DetectorResult("running", f"PR #{spec['pr']} open ({d.get('mergeable','?').lower()})", now_iso(), "detector:pr_merged")
        return DetectorResult("blocked", f"PR #{spec['pr']} closed without merging", now_iso(), "detector:pr_merged")

    def d_register_tally_consistent(self, spec):
        reg = parse_register(self._register_text())
        counts = register_counts(reg)["by_state"]
        label = {"OPEN": "OPEN", "CLOSED_ON_BRANCH": "CLOSED_ON_BRANCH", "DONE": "DONE", "CLOSED": "CLOSED",
                 "MEASURED in P6": "MEASURED", "PARTIAL": "PARTIAL"}
        diffs = []
        for name, n in reg["header"].items():
            cls = label.get(name)
            if cls is None:
                continue
            if counts.get(cls, 0) != n:
                diffs.append(f"{name}: header {n} vs rows {counts.get(cls, 0)}")
        for cls, n in counts.items():
            if n and cls not in {label.get(h) for h in reg["header"]}:
                diffs.append(f"{cls}: {n} rows, missing from header")
        if diffs:
            return DetectorResult("pending", "; ".join(diffs)[:300], now_iso(), "detector:register_tally_consistent")
        return DetectorResult("done", "header tallies match the rows", now_iso(), "detector:register_tally_consistent", 1.0)

    def d_register_wellformed(self, spec):
        reg = parse_register(self._register_text())
        if reg["malformed"]:
            return DetectorResult("pending", "malformed rows: " + ", ".join(reg["malformed"]), now_iso(), "detector:register_wellformed")
        return DetectorResult("done", f"all {len(reg['rows'])} rows well-formed", now_iso(), "detector:register_wellformed", 1.0)

    def d_register_rows_closed(self, spec):
        reg = parse_register(self._register_text())
        want = spec["rows"]
        missing = [r for r in want if r not in reg["rows"]]
        if missing:
            return DetectorResult("error", "rows not in register: " + ", ".join(missing), now_iso(), "detector:register_rows_closed")
        closed = [r for r in want if reg["rows"][r]["state_class"] in ("CLOSED", "DONE")]
        partial = [r for r in want if reg["rows"][r]["state_class"] in ("PARTIAL", "IN_PROGRESS", "CLOSED_ON_BRANCH")]
        frac = len(closed) / len(want)
        detail = f"{len(closed)}/{len(want)} closed" + (f"; partial: {', '.join(partial)}" if partial else "")
        if len(closed) == len(want):
            return DetectorResult("done", detail, now_iso(), "detector:register_rows_closed", 1.0)
        status = "running" if (closed or partial) else "pending"
        return DetectorResult(status, detail, now_iso(), "detector:register_rows_closed", frac)

    def d_main_file_contains(self, spec):
        self._fetch_main()
        rc, out = _run(["git", "show", f"origin/main:{spec['path']}"], cwd=self.cfg.repo, timeout=60)
        if rc != 0:
            return DetectorResult("error", f"cannot read {spec['path']} on main", now_iso(), "detector:main_file_contains")
        if re.search(spec["pattern"], out):
            return DetectorResult("done", f"{os.path.basename(spec['path'])} on main mentions it", now_iso(), "detector:main_file_contains", 1.0)
        return DetectorResult("pending", f"not yet in {os.path.basename(spec['path'])} on main", now_iso(), "detector:main_file_contains")

    def d_main_has_file(self, spec):
        self._fetch_main()
        rc, _ = _run(["git", "cat-file", "-e", f"origin/main:{spec['path']}"], cwd=self.cfg.repo, timeout=30)
        if rc == 0:
            return DetectorResult("done", f"{spec['path']} is on main", now_iso(), "detector:main_has_file", 1.0)
        return DetectorResult("pending", f"{os.path.basename(spec['path'])} not on main", now_iso(), "detector:main_has_file")

    def d_branch_merged(self, spec):
        self._fetch_main()
        _run(["git", "fetch", "-q", "origin", spec["ref"].replace("origin/", "")], cwd=self.cfg.repo, timeout=90)
        rc, _ = _run(["git", "merge-base", "--is-ancestor", spec["ref"], "origin/main"], cwd=self.cfg.repo, timeout=30)
        if rc == 0:
            return DetectorResult("done", f"{spec['ref']} is merged into main", now_iso(), "detector:branch_merged", 1.0)
        rc2, n = _run(["git", "rev-list", "--count", f"origin/main..{spec['ref']}"], cwd=self.cfg.repo, timeout=30)
        return DetectorResult("pending", f"{n.strip() if rc2 == 0 else '?'} commits not on main", now_iso(), "detector:branch_merged")

    def d_db_columns_exist(self, spec):
        found = []
        for table, col in spec["columns"]:
            rows = self._psql("select count(*) from information_schema.columns "
                              f"where table_name='{table}' and column_name='{col}'")
            found.append(bool(rows and rows[0][0] == "1"))
        n = sum(found)
        if n == len(found):
            return DetectorResult("done", "all columns present in production", now_iso(), "detector:db_columns_exist", 1.0)
        return DetectorResult("pending" if n == 0 else "running", f"{n}/{len(found)} columns present in production",
                              now_iso(), "detector:db_columns_exist", n / len(found))

    def d_levels_elevated(self, spec):
        """Family-aware since v1.3 (arch §6.4/§11.7): `exclude: "family_set"` drops every asset in
        every `family_*` list of `FAMILY_ASSETS.json` from the wave's completion count, so a family
        asset (or its reader) waiting on its own family session never blocks an otherwise-complete
        wave. Until FAMILY_ASSETS.json is frozen at J1 (E6.3) this reads `pending`, never `done` —
        a wave that claims `exclude: family_set` cannot honestly complete before the exclusion list
        it depends on exists."""
        lo, hi = spec["levels"]
        levels = dag_levels(self)
        exclude: set[str] = set()
        if spec.get("exclude") == "family_set":
            fam = self._family_assets()
            if fam is None:
                return DetectorResult("pending", "FAMILY_ASSETS.json not yet on main (frozen at J1/E6.3); "
                                                 "cannot honestly exclude the family set yet",
                                      now_iso(), "detector:levels_elevated")
            exclude = self._family_set_union(fam, "family_set")
        assets = [a for a, lv in levels.items() if lo <= lv <= hi and a not in exclude]
        if not assets:
            return DetectorResult("error", f"no assets at levels {lo}–{hi} after excluding the family set",
                                  now_iso(), "detector:levels_elevated")
        elevated = elevated_assets(self.cfg)
        n = sum(1 for a in assets if a in elevated)
        excl_note = f"; {len(exclude)} family/reader asset(s) excluded" if exclude else ""
        detail = f"{n}/{len(assets)} assets elevated (proxy: ≥1 certification and no open gap rows){excl_note}"
        if n == len(assets):
            return DetectorResult("done", detail, now_iso(), "detector:levels_elevated", 1.0)
        return DetectorResult("running" if n else "pending", detail, now_iso(), "detector:levels_elevated", n / len(assets))

    # -- v1.3 additions (arch §11.7, built by L.13) --------------------------------------------

    def d_prs_merged(self, spec):
        try:
            prs, unresolved = self._resolved_pr_numbers(spec)
        except RuntimeError as exc:
            return DetectorResult("error", f"gh: {str(exc)[:200]}", now_iso(), "detector:prs_merged")
        total = len(prs) + len(unresolved)
        if total == 0:
            return DetectorResult("pending", PARAMS_NOT_SET, now_iso(), "detector:prs_merged")
        merged, open_, closed = [], [], []
        for pr in prs:
            rc, out = _run(["gh", "pr", "view", str(pr), "--json", "state,mergedAt"], cwd=self.cfg.repo, timeout=60)
            if rc != 0:
                return DetectorResult("error", f"gh: {out.strip()[:160]}", now_iso(), "detector:prs_merged")
            d = json.loads(out)
            (merged if d["state"] == "MERGED" else open_ if d["state"] == "OPEN" else closed).append(pr)
        frac = len(merged) / total
        if len(merged) == total and not unresolved:
            return DetectorResult("done", f"all {total} PRs merged", now_iso(), "detector:prs_merged", 1.0)
        detail = f"{len(merged)}/{total} merged"
        if unresolved:
            detail += f"; no PR yet for head ref(s): {', '.join(unresolved)}"
        if open_:
            detail += f"; open: {open_}"
        if closed:
            detail += f"; closed without merging: {closed}"
            return DetectorResult("blocked", detail, now_iso(), "detector:prs_merged", frac)
        return DetectorResult("running" if merged or open_ else "pending", detail, now_iso(), "detector:prs_merged", frac)

    def d_main_has_files(self, spec):
        paths = spec.get("paths") or []
        if not paths:
            return DetectorResult("pending", PARAMS_NOT_SET, now_iso(), "detector:main_has_files")
        self._fetch_main()
        missing = [p for p in paths if _run(["git", "cat-file", "-e", f"origin/main:{p}"],
                                            cwd=self.cfg.repo, timeout=30)[0] != 0]
        n = len(paths) - len(missing)
        if not missing:
            return DetectorResult("done", f"all {len(paths)} paths on main", now_iso(), "detector:main_has_files", 1.0)
        shown = ", ".join(missing[:5]) + ("…" if len(missing) > 5 else "")
        detail = f"{n}/{len(paths)} paths on main; missing: {shown}"
        return DetectorResult("running" if n else "pending", detail, now_iso(), "detector:main_has_files", n / len(paths))

    def d_scorecard_pass(self, spec):
        ref, path, tests = spec.get("ref"), spec.get("path"), spec.get("tests") or []
        if not ref or not path or not tests:
            return DetectorResult("pending", PARAMS_NOT_SET, now_iso(), "detector:scorecard_pass")
        if ref == "origin/main" or ref.startswith("origin/"):
            self._fetch_main()
        rc, out = _run(["git", "show", f"{ref}:{path}"], cwd=self.cfg.repo, timeout=60)
        if rc != 0:
            return DetectorResult("pending", f"scorecard not yet at {path} on {ref}", now_iso(), "detector:scorecard_pass")
        data = json.loads(out)
        results = data.get("tests") or data.get("results") or {}
        commit = data.get("inspector_commit") or data.get("commit")
        missing = [t for t in tests if str(results.get(t, "")).upper() != "PASS"]
        n = len(tests) - len(missing)
        if not commit:
            return DetectorResult("pending", "scorecard names no inspector commit", now_iso(), "detector:scorecard_pass", n / len(tests) if n else None)
        if missing:
            detail = f"{n}/{len(tests)} PASS on {ref}; missing/failing: {', '.join(missing)}"
            return DetectorResult("running" if n else "pending", detail, now_iso(), "detector:scorecard_pass", n / len(tests))
        return DetectorResult("done", f"all {len(tests)} tests PASS on {ref}; inspector commit {commit}",
                              now_iso(), "detector:scorecard_pass", 1.0)

    def d_migrations_applied(self, spec):
        numbers = spec.get("numbers") or []
        if not numbers:
            return DetectorResult("pending", PARAMS_NOT_SET, now_iso(), "detector:migrations_applied")
        nums = [int(n) for n in numbers]
        pattern = "|".join(f"^{n}_" for n in nums)
        rows = self._psql(f"select filename from _migrations_applied where filename ~ '{pattern}'")
        applied = set()
        for r in rows:
            if r and r[0]:
                m = re.match(r"^(\d+)_", r[0])
                if m:
                    applied.add(int(m.group(1)))
        missing = [n for n in nums if n not in applied]
        n_applied = len(nums) - len(missing)
        if not missing:
            return DetectorResult("done", f"all {len(nums)} migrations applied", now_iso(), "detector:migrations_applied", 1.0)
        detail = f"{n_applied}/{len(nums)} applied; missing: {missing}"
        return DetectorResult("running" if n_applied else "pending", detail, now_iso(), "detector:migrations_applied", n_applied / len(nums))

    def d_register_rows_state(self, spec):
        """Review pass 2 (R244-deferred finding, substance #10/consistency #9): a row read as
        DEFERRED is not, by itself, evidence that the withholding it claims is actually in force or
        that the fix it defers to has landed — both are independently verifiable and, when the spec
        pins them, are now verified before a DEFERRED row counts as satisfying `states`. Neither
        `deferred_withholding_entry` nor `deferred_pr` is required: omit both and every DEFERRED row
        counts exactly as before (this generic detector backs many items, not only the R244 one)."""
        rows, states = spec.get("rows") or [], spec.get("states") or []
        if not rows or not states:
            return DetectorResult("pending", PARAMS_NOT_SET, now_iso(), "detector:register_rows_state")
        reg = parse_register(self._register_text())
        missing = [r for r in rows if r not in reg["rows"]]
        if missing:
            return DetectorResult("error", "rows not in register: " + ", ".join(missing), now_iso(), "detector:register_rows_state")

        withholding_entry = spec.get("deferred_withholding_entry")
        withholding_path = spec.get("deferred_withholding_path") or DEFAULT_WITHHOLDING_REL_PATH
        deferred_pr = spec.get("deferred_pr")

        ok, notes = [], []
        for r in rows:
            sc = reg["rows"][r]["state_class"]
            if sc not in states:
                continue
            if sc != "DEFERRED":
                ok.append(r)
                continue
            if withholding_entry and not self._withholding_has_entry(withholding_path, withholding_entry):
                notes.append(f"{r}: DEFERRED but withholding entry '{withholding_entry}' not found at {withholding_path}")
                continue
            if deferred_pr is not None:
                rc, out = _run(["gh", "pr", "view", str(deferred_pr), "--json", "state"], cwd=self.cfg.repo, timeout=60)
                if rc != 0:
                    notes.append(f"{r}: DEFERRED but its fix PR #{deferred_pr} could not be checked ({out.strip()[:100]})")
                    continue
                if json.loads(out).get("state") != "MERGED":
                    notes.append(f"{r}: DEFERRED but its fix PR #{deferred_pr} is not merged")
                    continue
            ok.append(r)

        n = len(ok)
        if n == len(rows):
            return DetectorResult("done", f"all {len(rows)} rows in {states}", now_iso(), "detector:register_rows_state", 1.0)
        bad = [f"{r}={reg['rows'][r]['state_class']}" for r in rows if r not in ok]
        detail = f"{n}/{len(rows)} in {states}; not yet: {', '.join(bad)}"
        if notes:
            detail += "; " + "; ".join(notes)
        return DetectorResult("running" if n else "pending", detail, now_iso(), "detector:register_rows_state", n / len(rows))

    def d_register_freeze_clean(self, spec):
        """Review pass 2 (substance #10c): a register that fails to parse (a table-layout/format
        change, an empty file, a bad ref) must never read `done` just because it happens to yield
        zero BLOCKS_FREEZE rows — that is indistinguishable from "every blocker really is closed"
        unless the register actually parsed at least some rows. Also names the ref/commit this
        result is computed from, so "the register was actually read at the pinned ref" is an
        auditable fact in the detail, not an assumption."""
        allow_deferred = set(spec.get("allow_deferred") or [])
        ref = _nikasha_ref()
        rc, ref_out = _run(["git", "-C", self.cfg.nikasha_root, "rev-parse", ref], timeout=15)
        if rc != 0:
            return DetectorResult("error", f"cannot resolve register ref {ref}: {ref_out.strip()[:160]}",
                                  now_iso(), "detector:register_freeze_clean")
        ref_sha = ref_out.strip()
        reg = parse_register(self._register_text())
        if not reg["rows"]:
            return DetectorResult("error", f"register at {ref} ({ref_sha[:12]}) parsed zero rows — cannot "
                                           "distinguish 'no BLOCKS_FREEZE rows' from 'could not parse the "
                                           "register' (a layout/format change)", now_iso(), "detector:register_freeze_clean")
        blockers = {rid: r for rid, r in reg["rows"].items() if r["severity"].strip().upper().startswith("BLOCKS_FREEZE")}
        if not blockers:
            return DetectorResult("done", f"no BLOCKS_FREEZE rows among {len(reg['rows'])} parsed rows "
                                          f"(register {ref} at {ref_sha[:12]})", now_iso(), "detector:register_freeze_clean", 1.0)
        bad = []
        for rid, r in blockers.items():
            sc = r["state_class"]
            if sc in ("CLOSED", "DONE"):
                continue
            if sc == "DEFERRED" and rid in allow_deferred:
                continue
            bad.append(f"{rid}={sc}")
        n_ok = len(blockers) - len(bad)
        if not bad:
            return DetectorResult("done", f"all {len(blockers)} BLOCKS_FREEZE rows closed (register {ref} at {ref_sha[:12]})",
                                  now_iso(), "detector:register_freeze_clean", 1.0)
        detail = f"{n_ok}/{len(blockers)} BLOCKS_FREEZE rows clean; open: {', '.join(bad)} (register {ref} at {ref_sha[:12]})"
        return DetectorResult("running" if n_ok else "pending", detail, now_iso(), "detector:register_freeze_clean", n_ok / len(blockers))

    def d_monitor_check_ok(self, spec):
        check = spec.get("check")
        if not check:
            return DetectorResult("pending", PARAMS_NOT_SET, now_iso(), "detector:monitor_check_ok")
        gov_dir = os.path.join(self.cfg.repo, "platform", "scripts", "governance")
        env = {**os.environ, "SUVARNA_HOME": self.cfg.home, "SUVARNA_DB_PORT": str(self.cfg.db_port)}
        if self.cfg.pgenv:
            env["SUVARNA_PGENV"] = self.cfg.pgenv
        rc, out = _run([sys.executable, "-m", "suvarna_tracker.monitor", "--once", "--json"],
                       cwd=gov_dir, timeout=60, env=env)
        report = json.loads(out)
        by_name = {c["name"]: c for c in report.get("checks", [])}
        c = by_name.get(check)
        if c is None:
            return DetectorResult("error", f"no such monitor check: {check}", now_iso(), "detector:monitor_check_ok")
        if c["status"] == "ok":
            return DetectorResult("done", f"{check}: {c['detail']}", now_iso(), "detector:monitor_check_ok", 1.0)
        status = "blocked" if c["status"] == "block" else "pending"
        return DetectorResult(status, f"{check}: {c['detail']}", now_iso(), "detector:monitor_check_ok")

    def d_deployed_contains(self, spec):
        """Review pass 2 (#5/#6/#7/#9): "contains" is git ancestry, never string equality or a
        substring test (other workstreams deploy to `main` too, and a tag that once matched can
        stop matching after any later, unrelated deploy). PRs may be pinned by number (`prs`) or by
        head ref (`head_refs`, resolved via `gh pr list`). `suvarna-build` is invoked by its full
        pinned path with no `--json` flag, and the serving key read is `deployed_sha`, never
        `web_sha` — the Track E brief's own contract (§1 E3.7, §5 E5.3, §8 E7)."""
        component = spec.get("component") or "job"
        try:
            prs, unresolved = self._resolved_pr_numbers(spec)
        except RuntimeError as exc:
            return DetectorResult("error", f"gh: {str(exc)[:200]}", now_iso(), "detector:deployed_contains")
        total = len(prs) + len(unresolved)
        if total == 0:
            return DetectorResult("pending", PARAMS_NOT_SET, now_iso(), "detector:deployed_contains")
        if unresolved:
            return DetectorResult("pending", f"no PR yet for head ref(s): {', '.join(unresolved)}",
                                  now_iso(), "detector:deployed_contains")
        merge_shas = []
        for pr in prs:
            rc, out = _run(["gh", "pr", "view", str(pr), "--json", "state,mergeCommit"], cwd=self.cfg.repo, timeout=60)
            if rc != 0:
                return DetectorResult("error", f"gh: {out.strip()[:160]}", now_iso(), "detector:deployed_contains")
            d = json.loads(out)
            if d["state"] != "MERGED":
                return DetectorResult("pending", f"PR #{pr} not merged yet", now_iso(), "detector:deployed_contains")
            sha = (d.get("mergeCommit") or {}).get("oid")
            if not sha:
                return DetectorResult("error", f"PR #{pr}: no merge commit recorded", now_iso(), "detector:deployed_contains")
            merge_shas.append(sha)
        rc, out = self._run_preflight()
        if rc != 0:
            return DetectorResult("error", f"suvarna-build --preflight: {out.strip()[:200]}", now_iso(), "detector:deployed_contains")
        try:
            pre = json.loads(out)
        except ValueError:
            return DetectorResult("error", f"suvarna-build --preflight: non-JSON output: {out.strip()[:160]}",
                                  now_iso(), "detector:deployed_contains")
        if component == "job":
            raw = pre.get("job_image_tag")
            if not raw:
                return DetectorResult("error", "preflight reported no job_image_tag", now_iso(), "detector:deployed_contains")
            descendant = _extract_trailing_sha(raw)
            if not descendant:
                return DetectorResult("error", f"job_image_tag has no trailing commit SHA: {raw[:80]}",
                                      now_iso(), "detector:deployed_contains")
            shown = raw[:24]
        else:
            descendant = pre.get("deployed_sha")
            if not descendant:
                return DetectorResult("error", "preflight reported no deployed_sha", now_iso(), "detector:deployed_contains")
            shown = descendant[:12]
        missing = []
        for s in merge_shas:
            try:
                if not self._is_ancestor(s, descendant):
                    missing.append(s)
            except RuntimeError as exc:
                return DetectorResult("error", f"ancestry check for {s[:12]}: {exc}", now_iso(), "detector:deployed_contains")
        n_ok = len(merge_shas) - len(missing)
        if not missing:
            return DetectorResult("done", f"{component} deploy ({shown}) contains all {total} merges (ancestry)",
                                  now_iso(), "detector:deployed_contains", 1.0)
        detail = f"{n_ok}/{total} merges are ancestors of the {component} deploy ({shown})"
        return DetectorResult("running" if n_ok else "pending", detail, now_iso(), "detector:deployed_contains", n_ok / total)

    def d_wave_deployed(self, spec):
        """Review pass 2 (#5/#6): ancestry, never substring; `suvarna-build` by full pinned path,
        no `--json`."""
        wave = spec.get("wave")
        if not wave:
            return DetectorResult("pending", PARAMS_NOT_SET, now_iso(), "detector:wave_deployed")
        landing_path = os.path.join(self.cfg.home, "evidence", wave, "LANDING.json")
        if not os.path.exists(landing_path):
            return DetectorResult("pending", f"no landing record yet at evidence/{wave}/LANDING.json", now_iso(), "detector:wave_deployed")
        with open(landing_path, encoding="utf-8") as f:
            landing = json.load(f)
        pr = landing.get("pr")
        if not pr:
            return DetectorResult("error", f"LANDING.json for {wave} names no PR", now_iso(), "detector:wave_deployed")
        rc, out = _run(["gh", "pr", "view", str(pr), "--json", "state,mergeCommit"], cwd=self.cfg.repo, timeout=60)
        if rc != 0:
            return DetectorResult("error", f"gh: {out.strip()[:160]}", now_iso(), "detector:wave_deployed")
        d = json.loads(out)
        if d["state"] != "MERGED":
            return DetectorResult("running", f"{wave} landing PR #{pr} open, not yet merged", now_iso(), "detector:wave_deployed", 0.5)
        sha = (d.get("mergeCommit") or {}).get("oid")
        if not sha:
            return DetectorResult("error", f"PR #{pr}: no merge commit recorded", now_iso(), "detector:wave_deployed")
        rc2, out2 = self._run_preflight()
        if rc2 != 0:
            return DetectorResult("error", f"suvarna-build --preflight: {out2.strip()[:200]}", now_iso(), "detector:wave_deployed")
        try:
            pre = json.loads(out2)
        except ValueError:
            return DetectorResult("error", f"suvarna-build --preflight: non-JSON output: {out2.strip()[:160]}",
                                  now_iso(), "detector:wave_deployed")
        tag = pre.get("job_image_tag") or ""
        descendant = _extract_trailing_sha(tag)
        if not descendant:
            return DetectorResult("error", f"job_image_tag has no trailing commit SHA: {tag[:80]}", now_iso(), "detector:wave_deployed")
        try:
            deployed = self._is_ancestor(sha, descendant)
        except RuntimeError as exc:
            return DetectorResult("error", f"ancestry check for {sha[:12]}: {exc}", now_iso(), "detector:wave_deployed")
        if deployed:
            return DetectorResult("done", f"{wave} landing PR #{pr} merged and deployed ({tag[:24]})", now_iso(), "detector:wave_deployed", 1.0)
        return DetectorResult("running", f"{wave} landing PR #{pr} merged ({sha[:12]}) but not yet an ancestor of the deployed tag ({tag[:24]})",
                              now_iso(), "detector:wave_deployed", 0.75)

    def d_assets_elevated(self, spec):
        set_name = spec.get("set")
        if not set_name:
            return DetectorResult("pending", PARAMS_NOT_SET, now_iso(), "detector:assets_elevated")
        fam = self._family_assets()
        if fam is None:
            return DetectorResult("pending", "FAMILY_ASSETS.json not yet on main (frozen at J1/E6.3)", now_iso(), "detector:assets_elevated")
        assets = self._family_set_union(fam, set_name)
        if not assets:
            return DetectorResult("error", f"no asset set '{set_name}' in FAMILY_ASSETS.json", now_iso(), "detector:assets_elevated")
        elevated = elevated_assets(self.cfg)
        n = sum(1 for a in assets if a in elevated)
        detail = f"{n}/{len(assets)} '{set_name}' assets elevated (proxy: ≥1 certification and no open gap row)"
        if n == len(assets):
            return DetectorResult("done", detail, now_iso(), "detector:assets_elevated", 1.0)
        return DetectorResult("running" if n else "pending", detail, now_iso(), "detector:assets_elevated", n / len(assets))

    def d_registry_coverage(self, spec):
        """Review pass 2 (substance #10a): an absent file reads `pending` (unchanged). An absent
        `uncovered_required_criteria`/`uncovered` *key* must also read `pending`, never `done` —
        the previous code treated "the report doesn't mention it" the same as "the report measured
        it and found nothing uncovered", so a malformed or partial report could read as fully
        covered by omission alone (CLAUDE.md §N.8: a signal without the check that could report
        otherwise is null, not green)."""
        try:
            text = _git_show_text(self.cfg.nikasha_root, REGISTRY_COVERAGE_REL_PATH)
        except RuntimeError:
            return DetectorResult("pending", "registry coverage report not yet on the ref (built by E6.1/E6.5)",
                                  now_iso(), "detector:registry_coverage")
        try:
            data = json.loads(text)
        except ValueError:
            return DetectorResult("error", "registry coverage report is not valid JSON", now_iso(), "detector:registry_coverage")
        if not isinstance(data, dict) or not ("uncovered_required_criteria" in data or "uncovered" in data):
            return DetectorResult("pending", "registry coverage report names no uncovered_required_criteria/"
                                             "uncovered key yet; an absent key is not evidence of coverage",
                                  now_iso(), "detector:registry_coverage")
        uncovered = data.get("uncovered_required_criteria") or data.get("uncovered") or []
        if uncovered:
            shown = ", ".join(str(u) for u in uncovered[:5]) + ("…" if len(uncovered) > 5 else "")
            return DetectorResult("running" if data.get("covered_cells") else "pending",
                                  f"{len(uncovered)} required criteria still at detector: NONE: {shown}",
                                  now_iso(), "detector:registry_coverage")
        return DetectorResult("done", "every core gate × layer cell is covered by a detector or a declared N/A rule",
                              now_iso(), "detector:registry_coverage", 1.0)

    def d_evidence_recent(self, spec):
        """A provisioning-evidence JSON written to disk at provisioning time, under
        `$SUVARNA_HOME/evidence/<path>` — never a live query. Built to replace the `builder_scope`
        Monitor check (Track E brief §8 E7.3), which cannot run as `suvarna_reader`: D6 withholds
        both `chart_grants.permission` and `profiles` from that login, so no live read can measure
        the builder's actual grant row (review pass 2 finding 3 / substance #14). The provisioning
        step (E7.2, run by the native with a privileged credential) writes the evidence file once;
        this detector only ever reads it back off disk, and reports `pending` — never `done` — for
        every way that file can fail to prove what it claims: missing, unparseable, missing a
        required key, or older than `max_age_hours`."""
        path, max_age_hours = spec.get("path"), spec.get("max_age_hours")
        required_keys = spec.get("required_keys") or []
        if not path or not max_age_hours:
            return DetectorResult("pending", PARAMS_NOT_SET, now_iso(), "detector:evidence_recent")
        full = os.path.join(self.cfg.home, "evidence", path)
        if not os.path.exists(full):
            return DetectorResult("pending", f"no evidence file yet at evidence/{path}", now_iso(), "detector:evidence_recent")
        try:
            mtime = os.path.getmtime(full)
            with open(full, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError) as exc:
            return DetectorResult("error", f"evidence/{path}: {type(exc).__name__}: {exc}"[:200], now_iso(), "detector:evidence_recent")
        if not isinstance(data, dict):
            return DetectorResult("error", f"evidence/{path} is not a JSON object", now_iso(), "detector:evidence_recent")
        missing_keys = [k for k in required_keys if data.get(k) in (None, "")]
        if missing_keys:
            return DetectorResult("pending", f"evidence/{path} missing key(s): {', '.join(missing_keys)}",
                                  now_iso(), "detector:evidence_recent")
        age_h = (time.time() - mtime) / 3600.0
        if age_h > max_age_hours:
            return DetectorResult("pending", f"evidence/{path} is {age_h:.1f}h old (over {max_age_hours}h)",
                                  now_iso(), "detector:evidence_recent")
        return DetectorResult("done", f"evidence/{path} is {age_h:.1f}h old, all required key(s) present",
                              now_iso(), "detector:evidence_recent", 1.0)

    def d_ledger_no_open_gap_on(self, spec):
        prefixes = spec.get("criteria_prefixes") or []
        if not prefixes:
            return DetectorResult("pending", PARAMS_NOT_SET, now_iso(), "detector:ledger_no_open_gap_on")
        ls = ledger_state(self.cfg)
        matching = [g for g in ls["open_gaps"] if str(g.get("criterion", "")).startswith(tuple(prefixes))]
        if not matching:
            return DetectorResult("done", f"no open gap rows on criteria {prefixes}", now_iso(), "detector:ledger_no_open_gap_on", 1.0)
        ids = [str(g.get("gap_id") or g.get("asset")) for g in matching]
        shown = ", ".join(ids[:5]) + ("…" if len(ids) > 5 else "")
        return DetectorResult("pending", f"{len(matching)} open gap row(s) on {prefixes}: {shown}",
                              now_iso(), "detector:ledger_no_open_gap_on")


# --------------------------------------------------------------------------------------------
# Shared measurements (also used by metrics)
# --------------------------------------------------------------------------------------------

_dag_cache: dict = {"at": 0.0, "levels": {}, "layer": {}}
_dag_lock = threading.Lock()


def dag_levels(det: Detectors) -> dict[str, int]:
    """Dependency level per active asset, from asset_registry.depends_on. Cached 10 minutes.

    Fix 6 (review #7): a dependency cycle is invalid registry data, not a valid level-0 result — it
    now raises RuntimeError naming the cycle's assets instead of silently returning 0 for the
    asset that closes the loop. Callers (the `levels_elevated` detector, the metrics refresh) let
    this propagate into their existing error-isolation paths, same as any other measurement failure.
    """
    with _dag_lock:
        if time.time() - _dag_cache["at"] < 600 and _dag_cache["levels"]:
            return dict(_dag_cache["levels"])
    rows = det._psql("select asset_id, layer, array_to_string(coalesce(depends_on,'{}'),',') "
                     "from asset_registry where is_active and dead_flag is not true")
    act = {r[0] for r in rows}
    deps = {r[0]: [d for d in (r[2].split(",") if len(r) > 2 and r[2] else []) if d in act] for r in rows}
    layer = {r[0]: r[1] for r in rows}
    lvl: dict[str, int] = {}

    def level(a, stack=()):
        if a in lvl:
            return lvl[a]
        if a in stack:
            cycle = stack[stack.index(a):] + (a,)
            raise RuntimeError(f"dependency cycle: {' -> '.join(cycle)}")
        lvl[a] = 0 if not deps[a] else 1 + max(level(d, stack + (a,)) for d in deps[a])
        return lvl[a]

    for a in act:
        level(a)
    with _dag_lock:
        _dag_cache.update(at=time.time(), levels=dict(lvl), layer=layer)
    return lvl


def ledger_state(cfg: Config) -> dict:
    """Open gap rows (last state per gap_id, not superseded) and certification rows — read from the
    committed ref (NIKASHA_REF, default HEAD), never the working tree (Fix 5)."""
    last = {}
    for line in _git_show_text(cfg.nikasha_root, GAPS_REL_PATH).splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("asset") == "_schema" or "gap_id" not in d:
            continue
        last[d["gap_id"]] = d
    open_gaps = [d for d in last.values() if d.get("state") in ("OPEN", "RE-OPENED")
                 and d.get("kind", "gap") == "gap" and not d.get("superseded_by")]
    certs = []
    for line in _git_show_text(cfg.nikasha_root, CERTS_REL_PATH).splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("asset") != "_schema":
            certs.append(d)
    return {"open_gaps": open_gaps, "certs": certs}


def elevated_assets(cfg: Config) -> set[str]:
    """Proxy for ELEVATED until the Nikaṣa tracker's own function is on main (E4.1)."""
    ls = ledger_state(cfg)
    with_open = {d["asset"] for d in ls["open_gaps"]}
    with_cert = {c.get("asset") for c in ls["certs"] if c.get("verdict") in ("PASS", "N/A")}
    return {a for a in with_cert if a not in with_open}


def port_open(port: int, host: str = "127.0.0.1", timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def power_source() -> str:
    try:
        rc, out = _run(["pmset", "-g", "batt"], timeout=5)
        if "AC Power" in out:
            return "ac"
        if "Battery Power" in out:
            m = re.search(r"(\d+)%", out)
            return f"battery {m.group(1)}%" if m else "battery"
    except Exception:
        pass
    return "unknown"
