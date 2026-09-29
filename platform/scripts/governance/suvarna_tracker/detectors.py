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
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
import types
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
    events_path: str | None = None  # override; default: <home>/run/EVENTS.jsonl (acks_from)


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

# Track E brief §8's exact FAMILY_ASSETS.json keys (CODE-4): a file that parses as JSON but is
# missing one of these is malformed/partial, never silently read as "that family's list is empty".
FAMILY_ASSETS_REQUIRED_KEYS = ("family_gochara", "family_sangam", "family_kshetra",
                               "family_readers_L3", "family_readers_L4", "family_readers_L5", "family_set")

# CODE-5: the registry coverage report's required keys. An absent key is never evidence of
# coverage — it is an error, never a `pending` read on the missing key alone (only a genuinely
# non-empty `uncovered_required_criteria` list, once every required key is present, is `pending`).
REGISTRY_COVERAGE_REQUIRED_KEYS = ("registry_revision", "inspector_commit", "covered_cells",
                                   "uncovered_required_criteria")

# CODE-8: until E6.3's exact-ELEVATED function (`asset_elevation_tracker.py`) is on the Nikaṣa ref
# and loadable, `levels_elevated`/`assets_elevated` read this, never the old one-certification-and-
# no-open-gap proxy (`elevated_assets()` below, kept only for the honestly-labelled `elevated_proxy`
# metric in server.py — never for a gate).
ASSET_ELEVATION_TRACKER_REL_PATH = "00_ARCHITECTURE/control/asset_elevation_tracker.py"
ELEVATION_NOT_WIRED_DETAIL = "unknown: exact ELEVATED not wired, E6.3t"


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


# CODE-17 (S13/C2): `run_tracker.sh` defaults NIKASHA_REF to `origin/campaign/nikasha-test` (the
# fold lanes land there as fast-forwards before the E4.3 cut-over, arch §12.7). A remote-tracking
# ref like that can only ever be as fresh as the last fetch, so every read against it fetches the
# named branch first — TTL-cached (300s, the same window `Detectors._fetch_main` uses) so a burst
# of reads across one poll cycle triggers at most one network call, never one per detector.
_nikasha_fetch_cache: dict = {"at": 0.0}
_nikasha_fetch_lock = threading.Lock()


def _fetch_nikasha_ref_if_needed(nikasha_root: str) -> None:
    """Fetch NIKASHA_REF's branch in `nikasha_root` when the ref is a remote-tracking one
    (`origin/<branch>`) and the TTL has expired. A ref that is not remote-tracking (`HEAD`, a local
    branch) needs no fetch and this is a no-op. Best-effort: a failed fetch is not raised here — the
    caller's own `git show`/`rev-parse` against whatever is locally present surfaces that failure on
    its own terms (consistent with `Detectors._fetch_main`, which is equally best-effort)."""
    ref = _nikasha_ref()
    if not ref.startswith("origin/"):
        return
    branch = ref[len("origin/"):]
    with _nikasha_fetch_lock:
        if time.time() - _nikasha_fetch_cache["at"] < 300:
            return
        _run(["git", "fetch", "-q", "origin", branch], cwd=nikasha_root, timeout=90)
        _nikasha_fetch_cache["at"] = time.time()


def _git_show_text(nikasha_root: str, rel_path: str) -> str:
    _fetch_nikasha_ref_if_needed(nikasha_root)
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
           "evidence_recent": 300,
           # v1.4 additions (review pass 2, §11.7)
           "fk_no_cascade": 600, "acks_from": 20, "main_protected": 300}

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

    def _family_assets_checked(self) -> tuple[dict | None, str | None]:
        """`_family_assets()` plus CODE-4's key validation. Returns `(data, None)` once every one of
        `FAMILY_ASSETS_REQUIRED_KEYS` (Track E brief §8) is present; `(None, None)` when the file is
        not on `origin/main` yet (unchanged pre-E6.3 state — the caller reads that as `pending`); or
        `(None, "<detail>")` when the file exists but is missing a required key — a malformed or
        partial file, never silently read as if the missing key's list were simply empty."""
        fam = self._family_assets()
        if fam is None:
            return None, None
        missing = [k for k in FAMILY_ASSETS_REQUIRED_KEYS if k not in fam]
        if missing:
            return None, f"FAMILY_ASSETS.json is missing required key(s): {', '.join(missing)}"
        return fam, None

    def _load_exact_elevated_assets_fn(self):
        """CODE-8: the E6.3 exact-ELEVATED function (`asset_elevation_tracker.py`), loaded fresh
        from `origin/main` every call (never cached, never the working tree — the same discipline
        `_family_assets()` uses for `FAMILY_ASSETS.json`, another J1/E6.3 control file). Returns a
        callable `fn(cfg) -> set[str]` (the same shape as the retired proxy `elevated_assets()`
        below), or `None` — never raises — when the module is not on main yet, fails to import, or
        does not expose an `elevated_assets` callable. A caller getting `None` reports `error`
        (`ELEVATION_NOT_WIRED_DETAIL`), never falls back to the proxy."""
        self._fetch_main()
        rc, out = _run(["git", "show", f"origin/main:{ASSET_ELEVATION_TRACKER_REL_PATH}"], cwd=self.cfg.repo, timeout=30)
        if rc != 0:
            return None
        module = types.ModuleType("_suvarna_e63_asset_elevation_tracker")
        try:
            exec(compile(out, ASSET_ELEVATION_TRACKER_REL_PATH, "exec"), module.__dict__)  # noqa: S102
        except Exception:  # noqa: BLE001 — a broken committed module is "not wired", not a crash
            return None
        fn = getattr(module, "elevated_assets", None)
        return fn if callable(fn) else None

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
        base = spec.get("base") or "main"
        for ref in spec.get("head_refs") or []:
            rc, out = _run(["gh", "pr", "list", "--state", "all", "--head", ref, "--base", base,
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

    PREFLIGHT_SCRIPT_MISSING = -1  # sentinel rc: the script itself is not there yet (CODE-1)

    def _run_preflight(self) -> tuple[int, str]:
        """`suvarna-build --preflight` via the pinned full path (review #6 — never a bare-name PATH
        lookup, never `--json`: neither is in the Track E brief's own contract). CODE-1: the script
        not existing yet (E7.2 not provisioned) is distinguished from every other failure —
        `PREFLIGHT_SCRIPT_MISSING` — so callers read that as `pending` ("not provisioned yet"),
        never `error` (a provisioning step that hasn't happened is an expected pre-J1 state, not a
        broken measurement)."""
        try:
            return _run([_suvarna_build_cmd(), "--preflight"], timeout=60)
        except FileNotFoundError:
            return self.PREFLIGHT_SCRIPT_MISSING, f"{_suvarna_build_cmd()}: not found"

    @staticmethod
    def _params_not_set_result(spec: dict, typ: str) -> "DetectorResult":
        """§11.7's rule has two distinct empty-input cases (CODE-3/C31): an *expected* input that
        does not exist yet (a file/PR not on the ref yet) reads `pending`; a *spec* deliberately left
        empty for a later item to pin (`pinned_by`) reads `unknown` (i.e. `error`) — it is not that
        the world hasn't caught up yet, it is that nobody has told the detector what to check. A spec
        with no `pinned_by` keeps the old `pending`/`PARAMS_NOT_SET` reading, unchanged."""
        pinned_by = spec.get("pinned_by")
        if pinned_by:
            return DetectorResult("error", f"unknown: parameters not set; pinned_by: {pinned_by}",
                                  now_iso(), f"detector:{typ}")
        return DetectorResult("pending", PARAMS_NOT_SET, now_iso(), f"detector:{typ}")

    @staticmethod
    def _running_job_commit(pre: dict) -> tuple[str | None, str | None, str | None]:
        """CODE-1: the running job commit is `job_sha` when the preflight names it, falling back to
        the trailing hex SHA of `job_image_tag` only when it does not (older preflight builds named
        only the tag). Returns `(sha, shown_for_detail, error)` — `error` is set (and the other two
        None) when neither key yields a usable commit."""
        sha = pre.get("job_sha")
        if sha:
            return sha, sha[:12], None
        raw = pre.get("job_image_tag")
        if not raw:
            return None, None, "preflight reported no job_sha or job_image_tag"
        sha = _extract_trailing_sha(raw)
        if not sha:
            return None, None, f"job_image_tag has no trailing commit SHA: {raw[:80]}"
        return sha, raw[:24], None

    def _gh_api_json(self, path: str, timeout: int = 30) -> tuple[object | None, str | None]:
        """One read-only `gh api <path>` call. Returns `(data, None)` on success or `(None,
        "<detail>")` on any failure (403, 404, or anything else) — the caller decides what that
        failure means for its own detector; this helper never guesses."""
        rc, out = _run(["gh", "api", path], cwd=self.cfg.repo, timeout=timeout)
        if rc != 0:
            return None, out.strip()[:200]
        try:
            return json.loads(out), None
        except ValueError:
            return None, f"non-JSON output: {out.strip()[:160]}"

    def _events_path(self) -> str:
        return self.cfg.events_path or os.path.join(self.cfg.home, "run", "EVENTS.jsonl")

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
        it depends on exists.

        CODE-8: ELEVATED itself is read only from the E6.3 exact function
        (`asset_elevation_tracker.py` at the committed Nikaṣa ref); until that module is on the ref
        and loadable, this reads `error` (`ELEVATION_NOT_WIRED_DETAIL`), never the old one-
        certification-and-no-open-gap proxy."""
        lo, hi = spec["levels"]
        elevated_fn = self._load_exact_elevated_assets_fn()
        if elevated_fn is None:
            return DetectorResult("error", ELEVATION_NOT_WIRED_DETAIL, now_iso(), "detector:levels_elevated")
        exclude: set[str] = set()
        if spec.get("exclude") == "family_set":
            fam, err = self._family_assets_checked()
            if err:
                return DetectorResult("error", err, now_iso(), "detector:levels_elevated")
            if fam is None:
                return DetectorResult("pending", "FAMILY_ASSETS.json not yet on main (frozen at J1/E6.3); "
                                                 "cannot honestly exclude the family set yet",
                                      now_iso(), "detector:levels_elevated")
            exclude = self._family_set_union(fam, "family_set")
        levels = dag_levels(self)
        assets = [a for a, lv in levels.items() if lo <= lv <= hi and a not in exclude]
        if not assets:
            return DetectorResult("error", f"no assets at levels {lo}–{hi} after excluding the family set",
                                  now_iso(), "detector:levels_elevated")
        elevated = elevated_fn(self.cfg)
        n = sum(1 for a in assets if a in elevated)
        excl_note = f"; {len(exclude)} family/reader asset(s) excluded" if exclude else ""
        detail = f"{n}/{len(assets)} assets elevated (exact, E6.3){excl_note}"
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
            return self._params_not_set_result(spec, "prs_merged")
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
            return self._params_not_set_result(spec, "main_has_files")
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
        """CODE-6 (Track E brief §5's scorecard schema): `tests[T]` is an object with a `verdict`
        field, never a bare string. Done requires, in addition to every listed test's verdict being
        PASS: the scorecard's own `generator_sha256` equals the sha256 of `git show <ref>:<generator>`
        (the committed generator, never a typed/trusted hash), and `inspector_commit` is an
        ancestor of `ref` (never merely present) — a scorecard whose generator has since changed, or
        whose inspector commit was later rewound past, must not read `done` on stale trust alone.

        B7 (review pass 3): when the plan item's own spec pins `generator` (the path the plan model
        expects the scorecard to have been generated by), the scorecard's own `data["generator"]`
        must equal that pinned path, or this is `pending`, never `done` — otherwise the hash check
        above only ever verifies whichever generator the scorecard *names itself*, which a scorecard
        naming any committed file (with that file's own real sha256) satisfies trivially, making the
        plan's pin dead. A spec with no `generator` key keeps the old, unpinned behaviour unchanged."""
        ref, path, tests = spec.get("ref"), spec.get("path"), spec.get("tests") or []
        if not ref or not path or not tests:
            return DetectorResult("pending", PARAMS_NOT_SET, now_iso(), "detector:scorecard_pass")
        if ref == "origin/main" or ref.startswith("origin/"):
            self._fetch_main()
        rc, out = _run(["git", "show", f"{ref}:{path}"], cwd=self.cfg.repo, timeout=60)
        if rc != 0:
            return DetectorResult("pending", f"scorecard not yet at {path} on {ref}", now_iso(), "detector:scorecard_pass")
        try:
            data = json.loads(out)
        except ValueError:
            return DetectorResult("error", f"scorecard at {path} on {ref} is not valid JSON", now_iso(), "detector:scorecard_pass")
        if not isinstance(data, dict):
            return DetectorResult("error", f"scorecard at {path} on {ref} is not a JSON object", now_iso(), "detector:scorecard_pass")

        generator, generator_sha256 = data.get("generator"), data.get("generator_sha256")
        inspector_commit, results = data.get("inspector_commit"), data.get("tests")
        missing_fields = [k for k, v in (("generator", generator), ("generator_sha256", generator_sha256),
                                         ("inspector_commit", inspector_commit)) if not v]
        if missing_fields:
            return DetectorResult("pending", f"scorecard at {path} on {ref} missing: {', '.join(missing_fields)}",
                                  now_iso(), "detector:scorecard_pass")
        if not isinstance(results, dict):
            return DetectorResult("error", f"scorecard at {path} on {ref}: 'tests' is not an object",
                                  now_iso(), "detector:scorecard_pass")

        pinned_generator = spec.get("generator")
        if pinned_generator and generator != pinned_generator:
            return DetectorResult("pending", f"scorecard's generator ({generator}) does not match the plan's "
                                             f"pinned generator ({pinned_generator})",
                                  now_iso(), "detector:scorecard_pass")

        rc2, gen_out = _run(["git", "show", f"{ref}:{generator}"], cwd=self.cfg.repo, timeout=60)
        if rc2 != 0:
            return DetectorResult("error", f"cannot read generator {generator} at {ref}: {gen_out.strip()[:160]}",
                                  now_iso(), "detector:scorecard_pass")
        actual_sha256 = hashlib.sha256(gen_out.encode("utf-8")).hexdigest()
        if actual_sha256 != generator_sha256:
            return DetectorResult("pending", f"scorecard's generator_sha256 does not match {generator} at {ref} "
                                             "(the committed generator has changed since the scorecard was run)",
                                  now_iso(), "detector:scorecard_pass")

        try:
            is_ancestor = self._is_ancestor(inspector_commit, ref)
        except RuntimeError as exc:
            return DetectorResult("error", f"ancestry check for inspector_commit {str(inspector_commit)[:12]}: {exc}",
                                  now_iso(), "detector:scorecard_pass")
        if not is_ancestor:
            return DetectorResult("pending", f"scorecard's inspector_commit {inspector_commit[:12]} is not an "
                                             f"ancestor of {ref}", now_iso(), "detector:scorecard_pass")

        def _verdict(t: str) -> str:
            entry = results.get(t)
            return str(entry.get("verdict", "")) if isinstance(entry, dict) else ""

        missing = [t for t in tests if _verdict(t).upper() != "PASS"]
        n = len(tests) - len(missing)
        if missing:
            detail = f"{n}/{len(tests)} PASS on {ref}; missing/failing: {', '.join(missing)}"
            return DetectorResult("running" if n else "pending", detail, now_iso(), "detector:scorecard_pass", n / len(tests))
        return DetectorResult("done", f"all {len(tests)} tests PASS on {ref}; generator hash verified; "
                                      f"inspector commit {inspector_commit[:12]} is an ancestor of {ref}",
                              now_iso(), "detector:scorecard_pass", 1.0)

    def d_migrations_applied(self, spec):
        numbers = spec.get("numbers") or []
        if not numbers:
            return self._params_not_set_result(spec, "migrations_applied")
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
        auditable fact in the detail, not an assumption.

        CODE-7 adds `expect_rows`: every row it names must actually be present in the parsed
        register, or that is an error too (a register that dropped a row it should still carry is
        exactly the same "cannot tell a real result from a parse/format miss" hazard). And, for the
        same reason, zero BLOCKS_FREEZE rows found among the parsed rows is now itself an error —
        never `done` — since it is indistinguishable from a severity-label or parse miss."""
        allow_deferred = set(spec.get("allow_deferred") or [])
        expect_rows = spec.get("expect_rows") or []
        # CODE-17: fetch before resolving the ref, so the reported ref_sha is the same commit
        # `_register_text()` (below) actually reads — not a stale local copy resolved a moment
        # before the fetch `_register_text()` would otherwise trigger.
        _fetch_nikasha_ref_if_needed(self.cfg.nikasha_root)
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
        missing_expect = [r for r in expect_rows if r not in reg["rows"]]
        if missing_expect:
            return DetectorResult("error", f"expected row(s) not in register: {', '.join(missing_expect)} "
                                           f"(register {ref} at {ref_sha[:12]})", now_iso(), "detector:register_freeze_clean")
        blockers = {rid: r for rid, r in reg["rows"].items() if r["severity"].strip().upper().startswith("BLOCKS_FREEZE")}
        if not blockers:
            return DetectorResult("error", f"no BLOCKS_FREEZE rows found among {len(reg['rows'])} parsed rows "
                                           f"(register {ref} at {ref_sha[:12]}) — cannot distinguish a genuinely "
                                           "clean register from a severity-label or parse miss", now_iso(),
                                  "detector:register_freeze_clean")
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
            return self._params_not_set_result(spec, "deployed_contains")
        if unresolved:
            return DetectorResult("pending", f"no PR yet for head ref(s): {', '.join(unresolved)}",
                                  now_iso(), "detector:deployed_contains")
        merge_shas = []
        for pr in prs:
            rc, out = _run(["gh", "pr", "view", str(pr), "--json", "state,mergeCommit"], cwd=self.cfg.repo, timeout=60)
            if rc != 0:
                return DetectorResult("error", f"gh: {out.strip()[:160]}", now_iso(), "detector:deployed_contains")
            d = json.loads(out)
            if d["state"] == "OPEN":
                return DetectorResult("pending", f"PR #{pr} not merged yet", now_iso(), "detector:deployed_contains")
            if d["state"] != "MERGED":
                # CODE-2: closed without merging is `blocked`, never lumped in with "still open".
                return DetectorResult("blocked", f"PR #{pr} closed without merging", now_iso(), "detector:deployed_contains")
            sha = (d.get("mergeCommit") or {}).get("oid")
            if not sha:
                return DetectorResult("error", f"PR #{pr}: no merge commit recorded", now_iso(), "detector:deployed_contains")
            merge_shas.append(sha)
        rc, out = self._run_preflight()
        if rc == self.PREFLIGHT_SCRIPT_MISSING:
            return DetectorResult("pending", f"suvarna-build not provisioned yet ({out})", now_iso(), "detector:deployed_contains")
        if rc != 0:
            return DetectorResult("error", f"suvarna-build --preflight: {out.strip()[:200]}", now_iso(), "detector:deployed_contains")
        try:
            pre = json.loads(out)
        except ValueError:
            return DetectorResult("error", f"suvarna-build --preflight: non-JSON output: {out.strip()[:160]}",
                                  now_iso(), "detector:deployed_contains")
        if component == "job":
            descendant, shown, err = self._running_job_commit(pre)
            if err:
                return DetectorResult("error", err, now_iso(), "detector:deployed_contains")
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

    # Review pass 3 (below-blocker): a landing PR's head ref must be a Suvarṇa landing branch for
    # this wave — otherwise `wave_deployed` trusts whatever PR number LANDING.json names, with
    # nothing checking that PR actually came from this campaign's own landing convention
    # (arch §12.2: "a PR to main comes from suvarna/land/<group>, cut from origin/main").
    WAVE_LANDING_HEAD_REF_PREFIX = "suvarna/land/"

    def d_wave_deployed(self, spec):
        """Review pass 2 (#5/#6): ancestry, never substring; `suvarna-build` by full pinned path,
        no `--json`.

        Review pass 3 (below-blocker): the landing PR's own head ref must be a Suvarṇa landing
        branch for this wave (`suvarna/land/<wave>...`) — a PR merged from anywhere else is not
        evidence this wave actually landed, whatever LANDING.json claims."""
        wave = spec.get("wave")
        # `wave` alone (no prs/head_refs/numbers/paths) is not one of CODE-3's enumerated empty-
        # params cases, so this keeps the unconditional `pending` reading.
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
        rc, out = _run(["gh", "pr", "view", str(pr), "--json", "state,mergeCommit,headRefName"], cwd=self.cfg.repo, timeout=60)
        if rc != 0:
            return DetectorResult("error", f"gh: {out.strip()[:160]}", now_iso(), "detector:wave_deployed")
        d = json.loads(out)
        if d["state"] != "MERGED":
            return DetectorResult("running", f"{wave} landing PR #{pr} open, not yet merged", now_iso(), "detector:wave_deployed", 0.5)
        sha = (d.get("mergeCommit") or {}).get("oid")
        if not sha:
            return DetectorResult("error", f"PR #{pr}: no merge commit recorded", now_iso(), "detector:wave_deployed")
        head_ref = str(d.get("headRefName") or "")
        expected_prefix = f"{self.WAVE_LANDING_HEAD_REF_PREFIX}{wave}"
        if not head_ref.startswith(expected_prefix):
            return DetectorResult("blocked", f"{wave} landing PR #{pr} head ref {head_ref!r} is not a "
                                             f"Suvarṇa landing branch for this wave (expected prefix "
                                             f"{expected_prefix!r})", now_iso(), "detector:wave_deployed")
        rc2, out2 = self._run_preflight()
        if rc2 == self.PREFLIGHT_SCRIPT_MISSING:
            return DetectorResult("pending", f"suvarna-build not provisioned yet ({out2})", now_iso(), "detector:wave_deployed")
        if rc2 != 0:
            return DetectorResult("error", f"suvarna-build --preflight: {out2.strip()[:200]}", now_iso(), "detector:wave_deployed")
        try:
            pre = json.loads(out2)
        except ValueError:
            return DetectorResult("error", f"suvarna-build --preflight: non-JSON output: {out2.strip()[:160]}",
                                  now_iso(), "detector:wave_deployed")
        descendant, shown, err = self._running_job_commit(pre)
        if err:
            return DetectorResult("error", err, now_iso(), "detector:wave_deployed")
        try:
            deployed = self._is_ancestor(sha, descendant)
        except RuntimeError as exc:
            return DetectorResult("error", f"ancestry check for {sha[:12]}: {exc}", now_iso(), "detector:wave_deployed")
        if deployed:
            return DetectorResult("done", f"{wave} landing PR #{pr} merged and deployed ({shown})", now_iso(), "detector:wave_deployed", 1.0)
        return DetectorResult("running", f"{wave} landing PR #{pr} merged ({sha[:12]}) but not yet an ancestor of the running commit ({shown})",
                              now_iso(), "detector:wave_deployed", 0.75)

    def d_assets_elevated(self, spec):
        """CODE-8: as `levels_elevated` — ELEVATED is read only from the E6.3 exact function; until
        it is on the ref and loadable this reads `error`, never the retired proxy."""
        set_name = spec.get("set")
        if not set_name:
            return DetectorResult("pending", PARAMS_NOT_SET, now_iso(), "detector:assets_elevated")
        elevated_fn = self._load_exact_elevated_assets_fn()
        if elevated_fn is None:
            return DetectorResult("error", ELEVATION_NOT_WIRED_DETAIL, now_iso(), "detector:assets_elevated")
        fam, err = self._family_assets_checked()
        if err:
            return DetectorResult("error", err, now_iso(), "detector:assets_elevated")
        if fam is None:
            return DetectorResult("pending", "FAMILY_ASSETS.json not yet on main (frozen at J1/E6.3)", now_iso(), "detector:assets_elevated")
        assets = self._family_set_union(fam, set_name)
        if not assets:
            return DetectorResult("error", f"no asset set '{set_name}' in FAMILY_ASSETS.json", now_iso(), "detector:assets_elevated")
        elevated = elevated_fn(self.cfg)
        n = sum(1 for a in assets if a in elevated)
        detail = f"{n}/{len(assets)} '{set_name}' assets elevated (exact, E6.3)"
        if n == len(assets):
            return DetectorResult("done", detail, now_iso(), "detector:assets_elevated", 1.0)
        return DetectorResult("running" if n else "pending", detail, now_iso(), "detector:assets_elevated", n / len(assets))

    def d_registry_coverage(self, spec):
        """CODE-5 (substance #10a, review pass 2): read from `origin/main` (arch §11.7's own table:
        the report is committed on main by E6.5's `asset_census.py --registry-check`) — the same
        discipline `_family_assets()` uses, not the Nikaṣa register/ledger ref. An absent file reads
        `pending` (unchanged). Every one of `registry_revision`, `inspector_commit`, `covered_cells`
        and `uncovered_required_criteria` must be present, or this is an `error`, never `pending` —
        an absent key is not evidence of coverage; a malformed or partial report must never read as
        fully covered by omission (CLAUDE.md §N.8: a signal without the check that could report
        otherwise is null, not green). Only once every key is present does a non-empty
        `uncovered_required_criteria` read `pending`/`running`."""
        self._fetch_main()
        rc, out = _run(["git", "show", f"origin/main:{REGISTRY_COVERAGE_REL_PATH}"], cwd=self.cfg.repo, timeout=30)
        if rc != 0:
            return DetectorResult("pending", "registry coverage report not yet on main (built by E6.1/E6.5)",
                                  now_iso(), "detector:registry_coverage")
        try:
            data = json.loads(out)
        except ValueError:
            return DetectorResult("error", "registry coverage report on main is not valid JSON", now_iso(), "detector:registry_coverage")
        if not isinstance(data, dict):
            return DetectorResult("error", "registry coverage report on main is not a JSON object", now_iso(), "detector:registry_coverage")
        missing = [k for k in REGISTRY_COVERAGE_REQUIRED_KEYS if k not in data]
        if missing:
            return DetectorResult("error", f"registry coverage report on main is missing required key(s): "
                                           f"{', '.join(missing)}; an absent key is not evidence of coverage",
                                  now_iso(), "detector:registry_coverage")
        uncovered = data["uncovered_required_criteria"]
        if not isinstance(uncovered, list):
            return DetectorResult("error", "registry coverage report's uncovered_required_criteria is not a list",
                                  now_iso(), "detector:registry_coverage")
        if uncovered:
            shown = ", ".join(str(u) for u in uncovered[:5]) + ("…" if len(uncovered) > 5 else "")
            return DetectorResult("running" if data.get("covered_cells") else "pending",
                                  f"{len(uncovered)} required criteria still at detector: NONE: {shown}",
                                  now_iso(), "detector:registry_coverage")
        return DetectorResult("done", f"every core gate × layer cell is covered by a detector or a declared N/A "
                                      f"rule (registry_revision {data['registry_revision']}, "
                                      f"covered_cells {data['covered_cells']})",
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

    # -- v1.4 additions (review pass 2, §11.7): fk_no_cascade, acks_from, main_protected ---------
    # Rule for all three, same as every other detector: read-only, empty params read `pending`
    # ("detector parameters not set yet"), never `done` without actually measuring.

    # CODE-9's original check (`confdeltype='c'`, ON DELETE CASCADE) plus the below-blocker finding
    # from review pass 3: a foreign key retyped to NO ACTION/RESTRICT (`confdeltype` 'a'/'r') is
    # just as dangerous as CASCADE for this specific rebuild — plan §9's own words are "would refuse
    # the L2 delete-then-insert" — so it is never silently read as `done` either. `allow:
    # set_null|no_fk` on the item's own params is the one escape: the plan may deliberately accept a
    # restricting FK for a referenced table it has separately decided is fine (e.g. because the real
    # remediation is SET NULL or dropping the FK outright, and a transient restrict reading is not
    # itself the gate).
    FK_RESTRICTING_TYPES = ("a", "r")  # NO ACTION, RESTRICT
    FK_RESTRICT_ALLOWED = ("set_null", "no_fk")

    def d_fk_no_cascade(self, spec):
        """CODE-9 (S3, F3.FK): no foreign key into `spec['referenced']` may still have
        `ON DELETE CASCADE` (`confdeltype = 'c'`) — read-only `pg_constraint`, as the reader.

        Review pass 3 (below-blocker F3.FK): a key retyped to NO ACTION/RESTRICT is `blocked`, not
        silently `done` — such a key would refuse the L2 delete-then-insert rebuild exactly as the
        CASCADE it replaced would over-delete, just in the opposite direction (an error instead of a
        silent cascade). `allow: set_null` or `allow: no_fk` on the item's spec is the one way past
        this for a referenced table the plan has separately decided is fine."""
        referenced = spec.get("referenced")
        if not referenced:
            return DetectorResult("pending", PARAMS_NOT_SET, now_iso(), "detector:fk_no_cascade")
        try:
            rows = self._psql("select conrelid::regclass, conname, confdeltype from pg_constraint "
                              f"where contype='f' and confrelid = '{referenced}'::regclass "
                              "and confdeltype in ('c','a','r')")
        except RuntimeError as exc:
            return DetectorResult("error", f"fk_no_cascade: {str(exc)[:200]}", now_iso(), "detector:fk_no_cascade")

        def _name(r):
            return f"{r[0]}.{r[1]}" if len(r) > 1 else str(r)

        cascade = [r for r in rows if len(r) > 2 and r[2] == "c"]
        restricting = [r for r in rows if len(r) > 2 and r[2] in self.FK_RESTRICTING_TYPES]

        if cascade:
            names = [_name(r) for r in cascade]
            shown = ", ".join(names[:8]) + ("…" if len(names) > 8 else "")
            return DetectorResult("pending", f"{len(cascade)} ON DELETE CASCADE foreign key(s) into "
                                             f"{referenced}: {shown}", now_iso(), "detector:fk_no_cascade")

        allow = spec.get("allow")
        if restricting and allow not in self.FK_RESTRICT_ALLOWED:
            names = [_name(r) for r in restricting]
            shown = ", ".join(names[:8]) + ("…" if len(names) > 8 else "")
            return DetectorResult("blocked", f"{len(restricting)} restricting (NO ACTION/RESTRICT) foreign "
                                             f"key(s) into {referenced}: {shown}; restrict would refuse the "
                                             f"MSR rebuild", now_iso(), "detector:fk_no_cascade")

        detail = f"no ON DELETE CASCADE foreign key into {referenced}"
        if restricting:
            detail += (f"; {len(restricting)} restricting foreign key(s) allowed by the item's own "
                       f"params (allow={allow!r})")
        return DetectorResult("done", detail, now_iso(), "detector:fk_no_cascade", 1.0)

    def d_acks_from(self, spec):
        """CODE-10 (S16, FI-8): done once the event log holds a `kind: note` from every named actor
        whose `detail` starts with `spec['marker']` (e.g. "ACK FI-8")."""
        actors, marker = spec.get("actors") or [], spec.get("marker")
        if not actors or not marker:
            return DetectorResult("pending", PARAMS_NOT_SET, now_iso(), "detector:acks_from")
        seen: set[str] = set()
        try:
            with open(self._events_path(), encoding="utf-8") as f:
                for raw in f:
                    line = raw.strip()
                    if not line:
                        continue
                    try:
                        ev = json.loads(line)
                    except ValueError:
                        continue
                    if not isinstance(ev, dict):
                        continue
                    actor = ev.get("actor")
                    if (ev.get("kind") == "note" and actor in actors
                            and str(ev.get("detail", "")).startswith(marker)):
                        seen.add(actor)
        except FileNotFoundError:
            pass  # no event log yet at all: nobody has acked (an expected input not yet there — pending, never error)
        except OSError as exc:
            return DetectorResult("error", f"acks_from: cannot read the event log: {exc}"[:200],
                                  now_iso(), "detector:acks_from")
        missing = [a for a in actors if a not in seen]
        n = len(actors) - len(missing)
        if not missing:
            return DetectorResult("done", f"acknowledged by all {len(actors)}: {', '.join(actors)}",
                                  now_iso(), "detector:acks_from", 1.0)
        detail = f"{n}/{len(actors)} acknowledged ({marker!r}); missing: {', '.join(missing)}"
        return DetectorResult("running" if n else "pending", detail, now_iso(), "detector:acks_from", n / len(actors))

    # CODE-11 near-blocker (review pass 3): `rules/branches/<branch>` names which rule fired but not
    # who may bypass it — that lives on the ruleset itself. `bypass_actors` is fetched per ruleset id
    # and checked against the native's own resolved user id, never trusted on the rule's say-so.
    def _ruleset_bypass_actors(self, ruleset_id) -> tuple[list[dict] | None, str | None]:
        data, err = self._gh_api_json(f"repos/{{owner}}/{{repo}}/rulesets/{ruleset_id}")
        if err is not None:
            return None, err
        if not isinstance(data, dict):
            return None, f"ruleset {ruleset_id} detail is not a JSON object"
        actors = data.get("bypass_actors")
        return (actors if isinstance(actors, list) else []), None

    def _resolve_user_id(self, login: str) -> tuple[int | None, str | None]:
        data, err = self._gh_api_json(f"users/{login}")
        if err is not None:
            return None, err
        if not isinstance(data, dict) or "id" not in data:
            return None, f"users/{login}: no id in response"
        return data["id"], None

    def _bypass_problems(self, ruleset_ids: list, bypass_only: str) -> tuple[list[str] | None, str | None]:
        """Returns `(problems, None)` — an empty list means every bypass actor on every named
        ruleset is the native's own login — or `(None, "<error>")` on any `gh api` failure. Never
        silently skips a ruleset id it was handed."""
        all_actors: list[dict] = []
        for rid in ruleset_ids:
            actors, err = self._ruleset_bypass_actors(rid)
            if err is not None:
                return None, f"gh api rulesets/{rid}: {err}"
            all_actors.extend(actors)
        if not all_actors:
            return [], None
        native_id, err2 = self._resolve_user_id(bypass_only)
        if err2 is not None:
            return None, f"gh api users/{bypass_only}: {err2}"
        extra = [a for a in all_actors
                if not (a.get("actor_type") == "User" and a.get("actor_id") == native_id)]
        if not extra:
            return [], None
        shown = ", ".join(f"{a.get('actor_type')}:{a.get('actor_id')}" for a in extra[:5])
        return [f"bypass actor(s) beyond {bypass_only}: {shown}"], None

    def _main_protected_from_rules(self, pr_rules: list[dict], branch: str, bypass_only: str) -> "DetectorResult":
        counts = [((r.get("parameters") or {}).get("required_approving_review_count") or 0) for r in pr_rules]
        best = max(counts) if counts else 0
        if best < 1:
            note = f"; bypass expected: {bypass_only} (not independently verifiable from this endpoint)"
            return DetectorResult("pending", f"{branch} has a ruleset pull-request rule but 0 required "
                                             f"approving reviews{note}", now_iso(), "detector:main_protected")

        ruleset_ids = sorted({r.get("ruleset_id") for r in pr_rules if r.get("ruleset_id") is not None},
                             key=str)
        if not ruleset_ids:
            note = f"; bypass expected: {bypass_only} (not independently verifiable — no ruleset_id on the rule)"
            return DetectorResult("done", f"{branch} protected by a ruleset pull-request rule requiring "
                                          f"{best} approving review(s){note}", now_iso(), "detector:main_protected", 1.0)
        problems, err = self._bypass_problems(ruleset_ids, bypass_only)
        if err is not None:
            return DetectorResult("error", err, now_iso(), "detector:main_protected")
        if problems:
            return DetectorResult("blocked", f"{branch} ruleset requires {best} approving review(s) but has "
                                             f"{'; '.join(problems)}", now_iso(), "detector:main_protected")
        note = f"; bypass checked: only {bypass_only} (or none)"
        return DetectorResult("done", f"{branch} protected by a ruleset pull-request rule requiring "
                                      f"{best} approving review(s){note}", now_iso(), "detector:main_protected", 1.0)

    def _main_protected_from_classic(self, protection: object, branch: str, bypass_only: str) -> "DetectorResult":
        note = f"; bypass expected: {bypass_only} (not independently verifiable from this endpoint)"
        if not isinstance(protection, dict):
            return DetectorResult("pending", f"no branch protection configured for {branch}",
                                  now_iso(), "detector:main_protected")
        required = ((protection.get("required_pull_request_reviews") or {}).get("required_approving_review_count") or 0)
        if protection.get("required_pull_request_reviews") and required >= 1:
            return DetectorResult("done", f"{branch} protected (classic) requiring {required} approving "
                                          f"review(s){note}", now_iso(), "detector:main_protected", 1.0)
        return DetectorResult("pending", f"{branch} branch protection does not yet require an approving "
                                         f"review{note}", now_iso(), "detector:main_protected")

    def d_main_protected(self, spec):
        """CODE-11 (S1, L.16b): `gh api repos/{owner}/{repo}/rules/branches/<branch>` (rulesets); if
        no pull-request rule applies there, fall back to the classic `.../branches/<branch>/protection`.
        Done once a pull-request rule requires at least one approving review; the bypass actor(s) are
        reported in the detail (this endpoint does not itself let us verify who they are). Any 403,
        404 or other failure on either call is `error`, never a silent 'not protected yet'."""
        branch, bypass_only = spec.get("branch"), spec.get("bypass_only")
        if not branch or not bypass_only:
            return DetectorResult("pending", PARAMS_NOT_SET, now_iso(), "detector:main_protected")
        rules, err = self._gh_api_json(f"repos/{{owner}}/{{repo}}/rules/branches/{branch}")
        if err is not None:
            return DetectorResult("error", f"gh api rules/branches/{branch}: {err}", now_iso(), "detector:main_protected")
        pr_rules = [r for r in (rules or []) if isinstance(r, dict) and r.get("type") == "pull_request"]
        if pr_rules:
            return self._main_protected_from_rules(pr_rules, branch, bypass_only)
        protection, err2 = self._gh_api_json(f"repos/{{owner}}/{{repo}}/branches/{branch}/protection")
        if err2 is not None:
            return DetectorResult("error", f"gh api branches/{branch}/protection: {err2}", now_iso(), "detector:main_protected")
        return self._main_protected_from_classic(protection, branch, bypass_only)


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
