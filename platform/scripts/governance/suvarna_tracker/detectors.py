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
import datetime as dt
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
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from urllib.parse import urlparse

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

# F7 (independent review): Track E §8 pins the E6.3 function's own interface as
# `elevated_assets(ref, repo)` — a pure function of a git ref and a repo checkout path, never of
# this tracker's own `Config` object (which the pre-fix callers passed instead; a conforming
# implementation raises on that call). `ELEVATED_ASSETS_REF` is the ref the function is always
# called with — the same ref its own module was just loaded from (`origin/main`), so "the function
# we run" and "the ref we tell it we're running at" never disagree.
ELEVATED_ASSETS_REF = "origin/main"

# F8 (independent review): the frozen wave-membership map (asset_id -> level int), committed
# alongside FAMILY_ASSETS.json at J1/E6.3. Once a plan item pins `spec['level_map']` (a rel path,
# defaulting to this constant when the value is simply truthy-but-not-a-path — see `_level_map`),
# wave membership comes from THIS file at the pinned `origin/main` ref, never the live registry
# DAG — and its absence at that ref is an error, never a silent fallback to the DAG.
DEFAULT_LEVEL_MAP_REL_PATH = "00_ARCHITECTURE/control/LEVEL_MAP.json"


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
    its own terms (consistent with `Detectors._fetch_main`, which is equally best-effort).

    F12 (independent review): the TTL cache's own `"at"` timestamp advances ONLY on a successful
    fetch (`rc == 0`) — the pre-fix code advanced it unconditionally, so a persistently failing
    fetch (network down, auth expired) would still suppress every retry for the next 300s, leaving
    every caller silently reading whatever was locally present arbitrarily far in the past. A
    failed fetch now retries on the very next call instead of waiting out the TTL it never earned."""
    ref = _nikasha_ref()
    if not ref.startswith("origin/"):
        return
    branch = ref[len("origin/"):]
    with _nikasha_fetch_lock:
        if time.time() - _nikasha_fetch_cache["at"] < 300:
            return
        rc, _ = _run(["git", "fetch", "-q", "origin", branch], cwd=nikasha_root, timeout=90)
        if rc == 0:
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
           "fk_no_cascade": 600, "acks_from": 20, "main_protected": 300,
           # peer_tracker_item: another campaign's own tracker instance (e.g. Pravāha)
           "peer_tracker_item": 60,
           # v1.5 additions (Astra review fold): evidence_verified, ci_job_passed, elevated_interface_ok
           "evidence_verified": 300, "ci_job_passed": 120, "elevated_interface_ok": 60}

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
        """F12 (independent review): a cached result older than 3× its own type's TTL is never
        served as-is — even a `done` — because that means the scheduled re-measurement (`poll`'s
        own `_due` bookkeeping) has stopped happening, for whatever reason (the poll loop stalled,
        a caller stopped polling this exact spec, …). Rather than keep answering with a
        potentially long-stale fact, this reads `unknown` past that point: an unmeasured-recently
        property is not a pass (CLAUDE.md §N.8). A result still within the 3×TTL window, or one
        whose own `checked_at` cannot be parsed (never invents staleness on that alone), is
        returned unchanged."""
        typ = spec.get("type", "?")
        with self._lock:
            res = self.results.get(self.key(spec))
        if res is None:
            return None
        try:
            checked = dt.datetime.fromisoformat(res.checked_at)
        except (ValueError, TypeError):
            return res
        if checked.tzinfo is None:
            checked = checked.replace(tzinfo=dt.timezone.utc)
        age_s = (dt.datetime.now(dt.timezone.utc) - checked).total_seconds()
        stale_after = self.TTL.get(typ, 60) * 3
        if age_s > stale_after:
            return DetectorResult("unknown", f"{res.detail} (stale: last measured {age_s:.0f}s ago, "
                                             f"over {stale_after}s without a re-measure)",
                                  res.checked_at, res.source, res.progress)
        return res

    # -- helpers ------------------------------------------------------------------------------
    def _fetch_main(self) -> None:
        """F12 (independent review): `_last_fetch` advances ONLY on a successful fetch (`rc ==
        0`) — the pre-fix code advanced it unconditionally, so a persistently failing fetch would
        still suppress every retry for 300s, leaving every `origin/main`-reading detector silently
        stuck on whatever was locally present arbitrarily far in the past. A failed fetch now
        retries on the very next call."""
        with self._fetch_lock:
            if time.time() - self._last_fetch < 300:
                return
            rc, _ = _run(["git", "fetch", "-q", "origin", "main"], cwd=self.cfg.repo, timeout=90)
            if rc == 0:
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
        """CODE-8 / F7: the E6.3 exact-ELEVATED function (`asset_elevation_tracker.py`), loaded
        fresh from `origin/main` every call (never cached, never the working tree — the same
        discipline `_family_assets()` uses for `FAMILY_ASSETS.json`, another J1/E6.3 control file).
        Returns a callable `fn(ref, repo) -> set[str]` — Track E §8's own pinned interface, never
        the retired one-argument `fn(cfg)` shape the pre-fix callers used (a conforming
        implementation raises on that call) — or `None`, never raising, when the module is not on
        main yet, fails to import, or does not expose an `elevated_assets` callable. A caller
        getting `None` reports `error` (`ELEVATION_NOT_WIRED_DETAIL`), never falls back to the
        retired proxy. Callers invoke the returned function as `fn(ELEVATED_ASSETS_REF, self.cfg.repo)`
        — never `fn(self.cfg)`."""
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

    def _level_map(self, level_map_spec) -> tuple[dict | None, str | None]:
        """F8: the frozen `LEVEL_MAP.json` (asset_id -> level int), read from the committed
        `origin/main` ref — never the live registry DAG once a spec pins this. `level_map_spec` is
        either the rel path itself (a string) or any other truthy value, which selects
        `DEFAULT_LEVEL_MAP_REL_PATH`. Returns `(data, None)` on success, or `(None, "<detail>")`
        when the file is absent or malformed at the ref — F8: absent is an ERROR here, never a
        silent fallback to the live DAG."""
        rel_path = level_map_spec if isinstance(level_map_spec, str) else DEFAULT_LEVEL_MAP_REL_PATH
        self._fetch_main()
        rc, out = _run(["git", "show", f"origin/main:{rel_path}"], cwd=self.cfg.repo, timeout=30)
        if rc != 0:
            return None, (f"LEVEL_MAP.json not found at origin/main:{rel_path} (F8: wave membership "
                          f"must come from the frozen level map, not the live registry DAG)")
        try:
            data = json.loads(out)
        except ValueError:
            return None, f"LEVEL_MAP.json at origin/main:{rel_path} is not valid JSON"
        if not isinstance(data, dict):
            return None, f"LEVEL_MAP.json at origin/main:{rel_path} is not a JSON object"
        return data, None

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

        CODE-8 / F7: ELEVATED itself is read only from the E6.3 exact function
        (`asset_elevation_tracker.py` at the committed Nikaṣa ref), called with its own pinned
        `(ref, repo)` interface (`ELEVATED_ASSETS_REF`, `self.cfg.repo`) — never the retired
        `fn(self.cfg)` shape; until that module is on the ref and loadable, this reads `error`
        (`ELEVATION_NOT_WIRED_DETAIL`), never the old one-certification-and-no-open-gap proxy.

        F8: `spec['level_map']`, when set, pins wave membership to the frozen `LEVEL_MAP.json` at
        the committed `origin/main` ref, never the live registry DAG — and its absence there is an
        `error`, never a silent fallback. Omitting `level_map` entirely keeps the live-DAG reading
        (backward compatible for items that have not been migrated to the frozen map yet)."""
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
        level_map_spec = spec.get("level_map")
        if level_map_spec:
            level_map, err = self._level_map(level_map_spec)
            if err:
                return DetectorResult("error", err, now_iso(), "detector:levels_elevated")
            levels = {a: lv for a, lv in level_map.items() if isinstance(lv, int)}
        else:
            levels = dag_levels(self)
        assets = [a for a, lv in levels.items() if lo <= lv <= hi and a not in exclude]
        if not assets:
            return DetectorResult("error", f"no assets at levels {lo}–{hi} after excluding the family set",
                                  now_iso(), "detector:levels_elevated")
        elevated = elevated_fn(ELEVATED_ASSETS_REF, self.cfg.repo)
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

    # F10 (independent review): a scorecard whose generator/inspector never change again would
    # otherwise certify the SAME PASS forever, however old — bounding staleness needs its own
    # timestamp check, independent of the generator-hash/ancestry checks (which only ever prove
    # "consistent with some point in the past", never "recent enough to trust today"). A week is
    # long enough for a legitimate CI cadence, short enough that a stale scorecard cannot outlive
    # an inspector change indefinitely.
    DEFAULT_SCORECARD_MAX_AGE_HOURS = 168

    def d_scorecard_pass(self, spec):
        """CODE-6 (Track E brief §5's scorecard schema) / F10 (independent review): `tests[T]` is
        an object with `verdict` AND `command` fields, never a bare string or a verdict alone —
        `command` is the evidence the test was actually *executed*, not merely typed in by hand.
        Done requires, in addition to every listed test's verdict being PASS: a `run_id` (any
        non-empty value — a scorecard with no run identity cannot be traced back to an actual
        execution); a `generated_at` timestamp no older than `spec['max_age_hours']` (default
        `DEFAULT_SCORECARD_MAX_AGE_HOURS`) — F10's own fix for the review's counterexample: an
        old PASS whose inspector has since changed while the generator has not must not remain
        `done` indefinitely, only until it goes stale; the scorecard's own `generator_sha256`
        equals the sha256 of `git show <ref>:<generator>` (the committed generator, never a typed/
        trusted hash); and `inspector_commit` is an ancestor of `ref` (never merely present) — a
        scorecard whose generator has since changed, or whose inspector commit was later rewound
        past, must not read `done` on stale trust alone.

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
        run_id, generated_at = data.get("run_id"), data.get("generated_at")
        missing_fields = [k for k, v in (("generator", generator), ("generator_sha256", generator_sha256),
                                         ("inspector_commit", inspector_commit), ("run_id", run_id),
                                         ("generated_at", generated_at)) if not v]
        if missing_fields:
            return DetectorResult("pending", f"scorecard at {path} on {ref} missing: {', '.join(missing_fields)}",
                                  now_iso(), "detector:scorecard_pass")
        if not isinstance(results, dict):
            return DetectorResult("error", f"scorecard at {path} on {ref}: 'tests' is not an object",
                                  now_iso(), "detector:scorecard_pass")

        # F10: freshness. Checked before the (more expensive) generator/ancestry git calls, same
        # discipline as every other cheap-first validation in this detector.
        try:
            generated_dt = dt.datetime.fromisoformat(str(generated_at))
        except ValueError:
            return DetectorResult("error", f"scorecard at {path} on {ref}: generated_at ({generated_at!r}) "
                                           "is not a valid ISO-8601 timestamp", now_iso(), "detector:scorecard_pass")
        if generated_dt.tzinfo is None:
            generated_dt = generated_dt.replace(tzinfo=dt.timezone.utc)
        max_age_hours = spec.get("max_age_hours") or self.DEFAULT_SCORECARD_MAX_AGE_HOURS
        age_hours = (dt.datetime.now(dt.timezone.utc) - generated_dt).total_seconds() / 3600.0
        if age_hours > max_age_hours:
            return DetectorResult("pending", f"scorecard at {path} on {ref} is {age_hours:.1f}h old "
                                             f"(over {max_age_hours}h; run_id {run_id}) — too stale to "
                                             "certify a currently-true result", now_iso(), "detector:scorecard_pass")

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

        # F10: every named test's entry must carry a `command` (the evidence it was actually
        # executed, not merely typed in by hand) as well as its `verdict` — a bare verdict alone
        # is never proof of execution.
        no_command = [t for t in tests if isinstance(results.get(t), dict) and not results[t].get("command")]
        if no_command:
            return DetectorResult("pending", f"scorecard at {path} on {ref}: test(s) missing a 'command' "
                                             f"field (cannot prove they were actually executed): "
                                             f"{', '.join(no_command)}", now_iso(), "detector:scorecard_pass")

        def _verdict(t: str) -> str:
            entry = results.get(t)
            return str(entry.get("verdict", "")) if isinstance(entry, dict) else ""

        missing = [t for t in tests if _verdict(t).upper() != "PASS"]
        n = len(tests) - len(missing)
        if missing:
            detail = f"{n}/{len(tests)} PASS on {ref}; missing/failing: {', '.join(missing)}"
            return DetectorResult("running" if n else "pending", detail, now_iso(), "detector:scorecard_pass", n / len(tests))
        return DetectorResult("done", f"all {len(tests)} tests PASS on {ref} (run_id {run_id}, "
                                      f"{age_hours:.1f}h old); generator hash verified; "
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
    # F13 (independent review): the landing PR's base branch must be exactly this — a PR merged
    # into anything else is not evidence main ever received this wave's changes at all.
    WAVE_LANDING_BASE_BRANCH = "main"

    def d_wave_deployed(self, spec):
        """Review pass 2 (#5/#6): ancestry, never substring; `suvarna-build` by full pinned path,
        no `--json`.

        Review pass 3 (below-blocker): the landing PR's own head ref must be a Suvarṇa landing
        branch for this wave (`suvarna/land/<wave>...`) — a PR merged from anywhere else is not
        evidence this wave actually landed, whatever LANDING.json claims.

        F13 (independent review): the pre-fix version checked ancestry and head-ref naming but
        neither (a) that the PR's *base* branch was actually `main` — a PR merged into some other
        branch proves nothing about what `main` received — nor (b) that the PR's changed files are
        exactly the packet LANDING.json recorded — a wave whose PR silently dropped, or silently
        added, files versus its own recorded packet must never read `deployed` on ancestry alone.
        Both are checked here, before the deploy/ancestry step; `LANDING.json` must name its own
        `packet` (the list of file paths this wave's landing was supposed to contain)."""
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
        packet = landing.get("packet")
        if not isinstance(packet, list) or not packet:
            return DetectorResult("error", f"LANDING.json for {wave} names no packet file list (F13: the "
                                           f"PR's changed files must equal the recorded packet)",
                                  now_iso(), "detector:wave_deployed")
        rc, out = _run(["gh", "pr", "view", str(pr), "--json", "state,mergeCommit,headRefName,baseRefName,files"],
                       cwd=self.cfg.repo, timeout=60)
        if rc != 0:
            return DetectorResult("error", f"gh: {out.strip()[:160]}", now_iso(), "detector:wave_deployed")
        d = json.loads(out)
        if d["state"] != "MERGED":
            return DetectorResult("running", f"{wave} landing PR #{pr} open, not yet merged", now_iso(), "detector:wave_deployed", 0.5)
        base_ref = str(d.get("baseRefName") or "")
        if base_ref != self.WAVE_LANDING_BASE_BRANCH:
            return DetectorResult("blocked", f"{wave} landing PR #{pr} base branch is {base_ref!r}, not "
                                             f"{self.WAVE_LANDING_BASE_BRANCH!r} (F13: a PR merged into "
                                             f"any other branch is not evidence main received this wave)",
                                  now_iso(), "detector:wave_deployed")
        sha = (d.get("mergeCommit") or {}).get("oid")
        if not sha:
            return DetectorResult("error", f"PR #{pr}: no merge commit recorded", now_iso(), "detector:wave_deployed")
        head_ref = str(d.get("headRefName") or "")
        expected_prefix = f"{self.WAVE_LANDING_HEAD_REF_PREFIX}{wave}"
        if not head_ref.startswith(expected_prefix):
            return DetectorResult("blocked", f"{wave} landing PR #{pr} head ref {head_ref!r} is not a "
                                             f"Suvarṇa landing branch for this wave (expected prefix "
                                             f"{expected_prefix!r})", now_iso(), "detector:wave_deployed")

        # F13: the PR's changed files must equal the recorded packet — exactly, not merely
        # overlap. A dropped or an extra file versus the recorded packet is never silently ignored.
        files = d.get("files")
        if not isinstance(files, list):
            return DetectorResult("error", f"PR #{pr}: gh reported no files list", now_iso(), "detector:wave_deployed")
        changed = {f.get("path") for f in files if isinstance(f, dict) and f.get("path")}
        packet_set = set(packet)
        if changed != packet_set:
            missing_from_pr = sorted(packet_set - changed)
            extra_in_pr = sorted(changed - packet_set)
            parts = []
            if missing_from_pr:
                parts.append(f"packet file(s) not in the PR: {missing_from_pr[:8]}")
            if extra_in_pr:
                parts.append(f"PR file(s) not in the recorded packet: {extra_in_pr[:8]}")
            return DetectorResult("blocked", f"{wave} landing PR #{pr} changed files do not equal the "
                                             f"recorded packet; {'; '.join(parts)}", now_iso(), "detector:wave_deployed")

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
        """CODE-8 / F7: as `levels_elevated` — ELEVATED is read only from the E6.3 exact function,
        called with its own pinned `(ref, repo)` interface, never the retired `fn(self.cfg)` shape;
        until it is on the ref and loadable this reads `error`, never the retired proxy."""
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
        elevated = elevated_fn(ELEVATED_ASSETS_REF, self.cfg.repo)
        n = sum(1 for a in assets if a in elevated)
        detail = f"{n}/{len(assets)} '{set_name}' assets elevated (exact, E6.3)"
        if n == len(assets):
            return DetectorResult("done", detail, now_iso(), "detector:assets_elevated", 1.0)
        return DetectorResult("running" if n else "pending", detail, now_iso(), "detector:assets_elevated", n / len(assets))

    def d_registry_coverage(self, spec):
        """CODE-5 (substance #10a, review pass 2) / F11 (independent review): read from
        `origin/main` (arch §11.7's own table: the report is committed on main by E6.5's
        `asset_census.py --registry-check`) — the same discipline `_family_assets()` uses, not the
        Nikaṣa register/ledger ref. An absent file reads `pending` (unchanged). Every one of
        `registry_revision`, `inspector_commit`, `covered_cells` and `uncovered_required_criteria`
        must be present, or this is an `error`, never `pending` — an absent key is not evidence of
        coverage; a malformed or partial report must never read as fully covered by omission
        (CLAUDE.md §N.8).

        F11 hardens this further: a *present but null/empty* `registry_revision` or
        `inspector_commit` is exactly as uninformative as an absent one — `error`, never `done` on
        a report that names no real revision at all. `covered_cells` must be a genuine positive
        integer — `covered_cells: 0` (or any non-positive value) paired with an empty
        `uncovered_required_criteria` is indistinguishable from "the report measured nothing",
        never `done` on that alone.

        When `spec['required_criteria']` (a list of criterion names this item specifically cares
        about) is given, `done` requires that NONE of them appear in the report's own
        `uncovered_required_criteria` — a cross-check against this item's own declared scope,
        never merely trusting the report's global list is empty. Omitting `required_criteria`
        keeps the old, unscoped behaviour (the whole report's `uncovered_required_criteria` must
        be empty)."""
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

        # F11: present-but-null is exactly as uninformative as absent.
        null_fields = [k for k in ("registry_revision", "inspector_commit")
                      if data.get(k) in (None, "")]
        if null_fields:
            return DetectorResult("error", f"registry coverage report on main has null/empty required "
                                           f"field(s): {', '.join(null_fields)}; a null revision is not "
                                           f"evidence of coverage", now_iso(), "detector:registry_coverage")
        covered_cells = data.get("covered_cells")
        if not isinstance(covered_cells, int) or isinstance(covered_cells, bool) or covered_cells <= 0:
            return DetectorResult("error", f"registry coverage report on main has covered_cells={covered_cells!r} "
                                           f"(must be a positive integer — a zero/absent count is not evidence "
                                           f"of coverage)", now_iso(), "detector:registry_coverage")

        uncovered = data["uncovered_required_criteria"]
        if not isinstance(uncovered, list):
            return DetectorResult("error", "registry coverage report's uncovered_required_criteria is not a list",
                                  now_iso(), "detector:registry_coverage")

        required_criteria = spec.get("required_criteria")
        if required_criteria:
            bad = [c for c in required_criteria if c in uncovered]
            if bad:
                shown = ", ".join(str(c) for c in bad[:5]) + ("…" if len(bad) > 5 else "")
                n_ok = len(required_criteria) - len(bad)
                return DetectorResult("running" if n_ok else "pending",
                                      f"{n_ok}/{len(required_criteria)} of this item's required criteria "
                                      f"covered; still uncovered: {shown}", now_iso(), "detector:registry_coverage",
                                      n_ok / len(required_criteria))
            return DetectorResult("done", f"all {len(required_criteria)} of this item's required criteria are "
                                          f"covered (registry_revision {data['registry_revision']}, "
                                          f"covered_cells {covered_cells})", now_iso(), "detector:registry_coverage", 1.0)

        if uncovered:
            shown = ", ".join(str(u) for u in uncovered[:5]) + ("…" if len(uncovered) > 5 else "")
            return DetectorResult("running", f"{len(uncovered)} required criteria still at detector: NONE: {shown}",
                                  now_iso(), "detector:registry_coverage")
        return DetectorResult("done", f"every core gate × layer cell is covered by a detector or a declared N/A "
                                      f"rule (registry_revision {data['registry_revision']}, "
                                      f"covered_cells {covered_cells})",
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

    # F9 (independent review): the pre-fix check ignored `spec['target']` entirely, queried only
    # CASCADE/NO ACTION/RESTRICT (never SET NULL/SET DEFAULT — both silently accepted for a
    # `no_fk` target), and its `allow` escape could approve a restricting key outright. F9's fix:
    # measure the item's own declared `target` — the delete rule the plan actually wants for every
    # foreign key into the referenced table — and block on ANY other rule, no escape hatch.
    FK_DELETE_TYPE_LABEL = {"c": "CASCADE", "a": "NO ACTION", "r": "RESTRICT", "n": "SET NULL", "d": "SET DEFAULT"}
    # target -> the one confdeltype code that satisfies it (None = no FK at all may exist).
    FK_TARGET_ACCEPTABLE_TYPE = {"no_fk": None, "set_null": "n", "set_default": "d"}
    # F9: the independent refusal guard the plan may separately require for this referenced table
    # (the recon's own C2 finding) — `spec['guard'] == 'present'` requires it to exist in the
    # database; `'absent'` or omitted means this item makes no claim about it either way.
    FK_GUARD_FUNCTION = "assert_l2_msr_delete_safe"

    def d_fk_no_cascade(self, spec):
        """F9 (S3, F3.FK, independent review): every foreign key into `spec['referenced']` must
        have exactly the delete rule `spec['target']` calls for (`no_fk` — no FK may exist at all;
        `set_null`; or `set_default`) — read-only `pg_constraint`, as the reader. Any other delete
        rule on any foreign key into the referenced table is `blocked`, never silently `done` —
        there is no `allow` escape (the pre-fix code's own hole: an item could approve a
        restricting key on its own say-so). When `spec['guard'] == 'present'`, the independent
        refusal-guard function (`assert_l2_msr_delete_safe`) must also exist in the database, or
        this is `pending`, never `done` on the FK shape alone."""
        referenced = spec.get("referenced")
        target = spec.get("target")
        if not referenced or not target:
            return DetectorResult("pending", PARAMS_NOT_SET, now_iso(), "detector:fk_no_cascade")
        if target not in self.FK_TARGET_ACCEPTABLE_TYPE:
            return DetectorResult("error", f"fk_no_cascade: unknown target {target!r} (expected one "
                                           f"of {sorted(self.FK_TARGET_ACCEPTABLE_TYPE)})",
                                  now_iso(), "detector:fk_no_cascade")
        try:
            rows = self._psql("select conrelid::regclass, conname, confdeltype from pg_constraint "
                              f"where contype='f' and confrelid = '{referenced}'::regclass")
        except RuntimeError as exc:
            return DetectorResult("error", f"fk_no_cascade: {str(exc)[:200]}", now_iso(), "detector:fk_no_cascade")

        def _name(r):
            return f"{r[0]}.{r[1]}" if len(r) > 1 else str(r)

        acceptable = self.FK_TARGET_ACCEPTABLE_TYPE[target]
        bad = [r for r in rows if len(r) > 2 and r[2] != acceptable]
        if bad:
            names = [f"{_name(r)} ({self.FK_DELETE_TYPE_LABEL.get(r[2], r[2])})" for r in bad]
            shown = ", ".join(names[:8]) + ("…" if len(names) > 8 else "")
            wants = "no foreign key at all" if target == "no_fk" else f"delete rule {self.FK_DELETE_TYPE_LABEL[acceptable]}"
            return DetectorResult("blocked", f"{len(bad)} foreign key(s) into {referenced} do not "
                                             f"satisfy target {target!r} ({wants}): {shown}",
                                  now_iso(), "detector:fk_no_cascade")

        guard = spec.get("guard")
        guard_note = ""
        if guard == "present":
            try:
                grows = self._psql(f"select count(*) from pg_proc where proname = '{self.FK_GUARD_FUNCTION}'")
            except RuntimeError as exc:
                return DetectorResult("error", f"fk_no_cascade guard check: {str(exc)[:200]}",
                                      now_iso(), "detector:fk_no_cascade")
            present = bool(grows and grows[0] and grows[0][0] not in ("0", ""))
            if not present:
                return DetectorResult("pending", f"target {target} satisfied for {referenced}, but the "
                                                 f"required refusal guard function "
                                                 f"{self.FK_GUARD_FUNCTION} is not present in the database",
                                      now_iso(), "detector:fk_no_cascade")
            guard_note = f"; refusal guard {self.FK_GUARD_FUNCTION} present"

        detail = f"every foreign key into {referenced} satisfies target {target!r}{guard_note}"
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

    # CODE-11 / F5 (independent review): `rules/branches/<branch>` names which rule fired but not
    # who may bypass it — that lives on the ruleset itself. `bypass_actors` is fetched per ruleset id
    # and checked against the RESOLVED set of allowed logins, never trusted on the rule's say-so and
    # never against a single hardcoded identity — N-28/N-29 (native rulings) mean the identity
    # actually allowed to bypass/merge is the swarm's own dedicated GitHub identity (post-CI-green,
    # post-gate-reviewer-accept), not "the native reviews" — so the allowed set is a param, resolved
    # here, never assumed.
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

    def _bypass_problems(self, ruleset_ids: list, allowed_logins: list[str]) -> tuple[list[str] | None, str | None]:
        """Returns `(problems, None)` — an empty list means every bypass actor on every named
        ruleset resolves to one of `allowed_logins` — or `(None, "<error>")` on any `gh api`
        failure. Never silently skips a ruleset id, or an allowed login, it was handed."""
        all_actors: list[dict] = []
        for rid in ruleset_ids:
            actors, err = self._ruleset_bypass_actors(rid)
            if err is not None:
                return None, f"gh api rulesets/{rid}: {err}"
            all_actors.extend(actors)
        if not all_actors:
            return [], None
        allowed_ids: set[int] = set()
        for login in allowed_logins:
            uid, err2 = self._resolve_user_id(login)
            if err2 is not None:
                return None, f"gh api users/{login}: {err2}"
            allowed_ids.add(uid)
        extra = [a for a in all_actors
                if not (a.get("actor_type") == "User" and a.get("actor_id") in allowed_ids)]
        if not extra:
            return [], None
        shown = ", ".join(f"{a.get('actor_type')}:{a.get('actor_id')}" for a in extra[:5])
        return [f"bypass actor(s) beyond {', '.join(allowed_logins)}: {shown}"], None

    # F5: proving the merge model means proving all four of these hold, together — a passing
    # review count alone (the pre-fix reading) proves nothing about who can skip it, whether CI is
    # actually required, or whether the branch can be force-pushed/deleted out from under its own
    # history. Each of these is an independent ruleset rule *type*; every one of them must be
    # present among the branch's rules (not merely the pull_request rule) before this reads `done`.
    MAIN_PROTECTED_REQUIRED_RULE_TYPES = ("required_status_checks", "non_fast_forward", "deletion")

    def _main_protected_from_rules(self, all_rules: list[dict], pr_rules: list[dict], branch: str,
                                   allowed_logins: list[str]) -> "DetectorResult":
        counts = [((r.get("parameters") or {}).get("required_approving_review_count") or 0) for r in pr_rules]
        best = max(counts) if counts else 0
        if best < 1:
            return DetectorResult("pending", f"{branch} has a ruleset pull-request rule but 0 required "
                                             f"approving reviews", now_iso(), "detector:main_protected")

        # F5: a pull-request rule with no ruleset_id cannot be traced to a ruleset detail endpoint
        # at all, so bypass/allowed-identity restriction is NOT independently verifiable — this is
        # `pending`, never `done` (the pre-fix code read this as `done` with bypass "not
        # independently verifiable" noted in the detail; that note is not proof).
        ruleset_ids = sorted({r.get("ruleset_id") for r in pr_rules if r.get("ruleset_id") is not None},
                             key=str)
        if not ruleset_ids:
            return DetectorResult("pending", f"{branch} has a ruleset pull-request rule with no "
                                             f"ruleset_id — bypass/allowed-identity restriction is not "
                                             f"independently verifiable this way; not proof of the merge "
                                             f"model (F5)", now_iso(), "detector:main_protected")

        missing_types = [t for t in self.MAIN_PROTECTED_REQUIRED_RULE_TYPES
                        if not any(isinstance(r, dict) and r.get("type") == t for r in all_rules)]
        if missing_types:
            return DetectorResult("pending", f"{branch} ruleset is missing required rule type(s): "
                                             f"{', '.join(missing_types)} (F5: required status checks, "
                                             f"no force-push, no deletion — not merely a review count)",
                                  now_iso(), "detector:main_protected")

        status_rule = next((r for r in all_rules if isinstance(r, dict) and r.get("type") == "required_status_checks"), None)
        contexts = ((status_rule.get("parameters") or {}).get("required_status_checks") or []) if status_rule else []
        if not contexts:
            return DetectorResult("pending", f"{branch} has a required_status_checks rule but it names no "
                                             f"status checks", now_iso(), "detector:main_protected")

        problems, err = self._bypass_problems(ruleset_ids, allowed_logins)
        if err is not None:
            return DetectorResult("error", err, now_iso(), "detector:main_protected")
        if problems:
            return DetectorResult("blocked", f"{branch} ruleset requires {best} approving review(s) but has "
                                             f"{'; '.join(problems)}", now_iso(), "detector:main_protected")
        return DetectorResult("done", f"{branch} protected by a ruleset requiring {best} approving "
                                      f"review(s), {len(contexts)} required status check(s), no "
                                      f"force-push, no deletion; bypass restricted to "
                                      f"{', '.join(allowed_logins)} (or none)",
                              now_iso(), "detector:main_protected", 1.0)

    def _main_protected_from_classic(self, protection: object, branch: str, allowed_logins: list[str]) -> "DetectorResult":
        """F5: classic branch protection has no per-actor bypass-actor endpoint at all (only
        rulesets do) — so it can never independently prove who may skip its own rules, whatever
        review count it requires. This is `pending`, never `done`; proving the merge model (F5)
        requires a ruleset."""
        if not isinstance(protection, dict):
            return DetectorResult("pending", f"no branch protection configured for {branch}",
                                  now_iso(), "detector:main_protected")
        required = ((protection.get("required_pull_request_reviews") or {}).get("required_approving_review_count") or 0)
        if protection.get("required_pull_request_reviews") and required >= 1:
            return DetectorResult("pending", f"{branch} protected (classic) requiring {required} approving "
                                             f"review(s), but classic protection has no bypass-actor "
                                             f"endpoint to independently verify who may skip it — a "
                                             f"ruleset is required to prove the merge model (F5)",
                                  now_iso(), "detector:main_protected")
        return DetectorResult("pending", f"{branch} branch protection does not yet require an approving "
                                         f"review", now_iso(), "detector:main_protected")

    def d_main_protected(self, spec):
        """CODE-11 (S1, L.16b) / F5 (independent review): `gh api
        repos/{owner}/{repo}/rules/branches/<branch>` (rulesets); if no pull-request rule applies
        there, fall back to the classic `.../branches/<branch>/protection` (which can only ever
        read `pending`, per F5 — see `_main_protected_from_classic`). `done` requires proving the
        whole merge model, together: an approving-review requirement, required status checks
        (CI-green), no force-push, no deletion, and every bypass actor resolving to one of
        `spec['allowed_logins']` — the swarm's own dedicated merge identity and/or the native's,
        never "the native reviews" alone (N-28/N-29). `allowed_logins` is a list; `bypass_only` (a
        single login) is accepted as a backward-compatible alias for `[bypass_only]`. Any 403, 404
        or other failure on any `gh api` call is `error`, never a silent 'not protected yet'."""
        branch = spec.get("branch")
        allowed_logins = spec.get("allowed_logins")
        if not allowed_logins:
            single = spec.get("bypass_only")
            allowed_logins = [single] if single else []
        if not branch or not allowed_logins:
            return DetectorResult("pending", PARAMS_NOT_SET, now_iso(), "detector:main_protected")
        rules, err = self._gh_api_json(f"repos/{{owner}}/{{repo}}/rules/branches/{branch}")
        if err is not None:
            return DetectorResult("error", f"gh api rules/branches/{branch}: {err}", now_iso(), "detector:main_protected")
        all_rules = [r for r in (rules or []) if isinstance(r, dict)]
        pr_rules = [r for r in all_rules if r.get("type") == "pull_request"]
        if pr_rules:
            return self._main_protected_from_rules(all_rules, pr_rules, branch, allowed_logins)
        protection, err2 = self._gh_api_json(f"repos/{{owner}}/{{repo}}/branches/{branch}/protection")
        if err2 is not None:
            return DetectorResult("error", f"gh api branches/{branch}/protection: {err2}", now_iso(), "detector:main_protected")
        return self._main_protected_from_classic(protection, branch, allowed_logins)

    def d_peer_tracker_item(self, spec):
        """Reads another campaign's tracker instance (the same tracker software; e.g. Pravāha at
        `http://127.0.0.1:8766/api/state`) and is `done` only when the named item's status there is
        exactly the expected status (`spec['expect']`, default `'done'`). `spec['evidence_required']`
        (default False), when true, also requires that item's own `evidence` field to be non-empty —
        a peer tracker reporting `done` with no evidence behind it is not itself proof (CLAUDE.md
        §N.8). An unreachable peer or a missing item is `pending`, never `error`/`done` — a peer
        tracker being briefly unreachable, or an item not yet on its plan, is an expected, transient
        state, not a broken measurement. A URL naming any host other than 127.0.0.1 is refused
        before any request is made — this detector never fetches off-loopback."""
        url, item_id = spec.get("url"), spec.get("item")
        if not url or not item_id:
            return DetectorResult("pending", PARAMS_NOT_SET, now_iso(), "detector:peer_tracker_item")
        try:
            host = urlparse(url).hostname
        except ValueError:
            return DetectorResult("error", f"unparseable peer tracker URL: {url}", now_iso(), "detector:peer_tracker_item")
        if host != PEER_TRACKER_ALLOWED_HOST:
            return DetectorResult("error", f"refused: peer tracker URL must be on "
                                           f"{PEER_TRACKER_ALLOWED_HOST!r} (got host {host!r})",
                                  now_iso(), "detector:peer_tracker_item")
        expect = spec.get("expect") or "done"
        evidence_required = bool(spec.get("evidence_required"))
        data, err = _peer_tracker_get(url)
        if err is not None:
            return DetectorResult("pending", f"peer tracker at {url} unreachable: {err}",
                                  now_iso(), "detector:peer_tracker_item")
        peer_item = _find_item_in_tracks(data, item_id)
        if peer_item is None:
            return DetectorResult("pending", f"item {item_id!r} not found in peer tracker at {url}",
                                  now_iso(), "detector:peer_tracker_item")
        status = peer_item.get("status")
        if status != expect:
            return DetectorResult("pending", f"{item_id} at {url} is {status!r}, expected {expect!r}",
                                  now_iso(), "detector:peer_tracker_item")
        if evidence_required and not peer_item.get("evidence"):
            return DetectorResult("pending", f"{item_id} at {url} is {expect!r} but has no evidence",
                                  now_iso(), "detector:peer_tracker_item")
        detail = f"{item_id} at {url} is {expect!r}" + (" with evidence" if evidence_required else "")
        return DetectorResult("done", detail, now_iso(), "detector:peer_tracker_item", 1.0)

    # -- v1.5 additions (Astra review fold, plan set v1.5): evidence_verified, ci_job_passed,
    # elevated_interface_ok ---------------------------------------------------------------------

    def d_evidence_verified(self, spec):
        """A provisioning/launch-gate evidence JSON written to disk at measurement time, under
        `$SUVARNA_HOME/evidence/<path>` — never a live query (same discipline as `evidence_recent`,
        which this generalizes). `done` requires every key in `spec['expect']` to be present in
        the evidence file with EXACTLY that value — never a truthy/non-empty check alone, since a
        gate like `{"refusal_path_present": false}` needs the FALSE reading, not merely "present".
        Every name in `spec['required']` (if given) must also be present, any value. When
        `spec['commit_key']`/`spec['commit']` pin a specific commit (a plan item's own way of
        binding its evidence to a specific control-release commit without hardcoding the value
        into the plan model — filled in later via `pinned_by`), the evidence file's own
        `commit_key` field must equal it, or this is `pending`, never `done`. An empty `commit`
        (not yet pinned) skips that one check, unaffected. `spec['max_age_hours']`, when given,
        is enforced exactly as `evidence_recent` does."""
        path = spec.get("path")
        expect = spec.get("expect")
        if not path or not isinstance(expect, dict) or not expect:
            return DetectorResult("pending", PARAMS_NOT_SET, now_iso(), "detector:evidence_verified")
        full = os.path.join(self.cfg.home, "evidence", path)
        if not os.path.exists(full):
            return DetectorResult("pending", f"no evidence file yet at evidence/{path}", now_iso(), "detector:evidence_verified")
        try:
            mtime = os.path.getmtime(full)
            with open(full, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError) as exc:
            return DetectorResult("error", f"evidence/{path}: {type(exc).__name__}: {exc}"[:200],
                                  now_iso(), "detector:evidence_verified")
        if not isinstance(data, dict):
            return DetectorResult("error", f"evidence/{path} is not a JSON object", now_iso(), "detector:evidence_verified")

        required = spec.get("required") or []
        missing_required = [k for k in required if k not in data]
        if missing_required:
            return DetectorResult("pending", f"evidence/{path} missing required key(s): {', '.join(missing_required)}",
                                  now_iso(), "detector:evidence_verified")

        commit_key, pinned_commit = spec.get("commit_key"), spec.get("commit")
        if commit_key and pinned_commit:
            actual_commit = data.get(commit_key)
            if actual_commit != pinned_commit:
                return DetectorResult("pending", f"evidence/{path}: {commit_key} ({actual_commit!r}) does "
                                                 f"not match the pinned commit ({pinned_commit!r})",
                                      now_iso(), "detector:evidence_verified")

        mismatched = [(k, data.get(k), v) for k, v in expect.items() if data.get(k) != v]
        if mismatched:
            shown = "; ".join(f"{k}={got!r} (expected {want!r})" for k, got, want in mismatched[:5])
            return DetectorResult("pending", f"evidence/{path} does not match expected: {shown}",
                                  now_iso(), "detector:evidence_verified")

        max_age_hours = spec.get("max_age_hours")
        if max_age_hours:
            age_h = (time.time() - mtime) / 3600.0
            if age_h > max_age_hours:
                return DetectorResult("pending", f"evidence/{path} is {age_h:.1f}h old (over {max_age_hours}h)",
                                      now_iso(), "detector:evidence_verified")

        return DetectorResult("done", f"evidence/{path} matches every expected field: {expect}",
                              now_iso(), "detector:evidence_verified", 1.0)

    def d_ci_job_passed(self, spec):
        """A named CI job, within a named GitHub Actions workflow, having actually RUN (never a
        text/file-existence match against the workflow's own YAML) and passed, on `origin/main`'s
        current HEAD commit, for a commit that already contains every one of `spec['paths']`.
        `spec['job']` is empty on every real item using this detector today (Track E has not yet
        named the exact job — see `pinned_by`); the CODE-3 unpinned-spec convention applies via
        `_params_not_set_result`, never a guess at which job to check."""
        workflow, job, paths = spec.get("workflow"), spec.get("job"), spec.get("paths") or []
        if not workflow or not job or not paths:
            return self._params_not_set_result(spec, "ci_job_passed")
        self._fetch_main()
        missing = [p for p in paths if _run(["git", "cat-file", "-e", f"origin/main:{p}"],
                                            cwd=self.cfg.repo, timeout=30)[0] != 0]
        if missing:
            shown = ", ".join(missing[:5])
            return DetectorResult("pending", f"path(s) not yet on main: {shown}", now_iso(), "detector:ci_job_passed")
        rc, head_out = _run(["git", "rev-parse", "origin/main"], cwd=self.cfg.repo, timeout=15)
        if rc != 0:
            return DetectorResult("error", f"cannot resolve origin/main: {head_out.strip()[:160]}",
                                  now_iso(), "detector:ci_job_passed")
        head_sha = head_out.strip()
        workflow_file = os.path.basename(workflow)
        runs_data, err = self._gh_api_json(f"repos/{{owner}}/{{repo}}/actions/workflows/{workflow_file}/"
                                           f"runs?head_sha={head_sha}&per_page=5")
        if err is not None:
            return DetectorResult("error", f"gh api workflow runs: {err}", now_iso(), "detector:ci_job_passed")
        runs = (runs_data or {}).get("workflow_runs") if isinstance(runs_data, dict) else None
        if not runs:
            return DetectorResult("pending", f"no CI run yet for {workflow_file} at origin/main ({head_sha[:12]})",
                                  now_iso(), "detector:ci_job_passed")
        run = runs[0]
        if run.get("status") != "completed":
            return DetectorResult("running", f"{workflow_file} run for {head_sha[:12]} still {run.get('status')}",
                                  now_iso(), "detector:ci_job_passed", 0.5)
        run_id = run.get("id")
        jobs_data, err2 = self._gh_api_json(f"repos/{{owner}}/{{repo}}/actions/runs/{run_id}/jobs")
        if err2 is not None:
            return DetectorResult("error", f"gh api run jobs: {err2}", now_iso(), "detector:ci_job_passed")
        jobs = (jobs_data or {}).get("jobs") if isinstance(jobs_data, dict) else None
        matching = next((j for j in (jobs or []) if isinstance(j, dict) and j.get("name") == job), None)
        if matching is None:
            return DetectorResult("error", f"no job named {job!r} in {workflow_file} run {run_id}",
                                  now_iso(), "detector:ci_job_passed")
        conclusion = matching.get("conclusion")
        if conclusion == "success":
            return DetectorResult("done", f"{workflow_file}/{job} passed on {head_sha[:12]} (run {run_id})",
                                  now_iso(), "detector:ci_job_passed", 1.0)
        if conclusion in ("failure", "cancelled", "timed_out"):
            return DetectorResult("blocked", f"{workflow_file}/{job} concluded {conclusion} on {head_sha[:12]} "
                                             f"(run {run_id})", now_iso(), "detector:ci_job_passed")
        return DetectorResult("running", f"{workflow_file}/{job} not yet concluded ({conclusion}) on "
                                         f"{head_sha[:12]} (run {run_id})", now_iso(), "detector:ci_job_passed", 0.5)

    def d_elevated_interface_ok(self, spec):
        """F7 (independent review, E6.3t): the pre-fix E6.3t check verified only that the module
        and a test file exist — never that the tracker's own caller could actually invoke the
        pinned `elevated_assets(ref, repo)` interface successfully. This detector does exactly
        that: loads the committed module (the same discipline `_load_exact_elevated_assets_fn`
        always uses) and calls it with the real, pinned interface at `spec['ref']` (default
        `ELEVATED_ASSETS_REF`) — `done` only when the call succeeds and returns a set/frozenset."""
        ref = spec.get("ref") or ELEVATED_ASSETS_REF
        elevated_fn = self._load_exact_elevated_assets_fn()
        if elevated_fn is None:
            return DetectorResult("error", ELEVATION_NOT_WIRED_DETAIL, now_iso(), "detector:elevated_interface_ok")
        try:
            result = elevated_fn(ref, self.cfg.repo)
        except TypeError as exc:
            return DetectorResult("blocked", f"elevated_assets does not accept the pinned (ref, repo) "
                                             f"interface: {exc}"[:200], now_iso(), "detector:elevated_interface_ok")
        except Exception as exc:  # noqa: BLE001 — a broken committed implementation is a real failure here
            return DetectorResult("error", f"elevated_assets(ref, repo) raised: {type(exc).__name__}: {exc}"[:200],
                                  now_iso(), "detector:elevated_interface_ok")
        if not isinstance(result, (set, frozenset)):
            return DetectorResult("blocked", f"elevated_assets(ref, repo) returned {type(result).__name__}, "
                                             f"not a set", now_iso(), "detector:elevated_interface_ok")
        return DetectorResult("done", f"elevated_assets({ref!r}, repo) called successfully via the real "
                                      f"tracker caller; returned {len(result)} asset id(s)",
                              now_iso(), "detector:elevated_interface_ok", 1.0)


# --------------------------------------------------------------------------------------------
# peer_tracker_item helpers (module-level, network-touching — no `self` needed)
# --------------------------------------------------------------------------------------------

PEER_TRACKER_ALLOWED_HOST = "127.0.0.1"
PEER_TRACKER_TIMEOUT = 3.0


def _peer_tracker_get(url: str) -> tuple[dict | None, str | None]:
    """One read-only GET against a peer tracker's `/api/state`-shaped endpoint (127.0.0.1 only —
    the caller has already refused any other host before this is ever called). Returns `(data,
    None)` on success or `(None, "<detail>")` on any failure — timeout, connection refused,
    non-JSON body, or a JSON body that is not an object."""
    try:
        with urllib.request.urlopen(url, timeout=PEER_TRACKER_TIMEOUT) as resp:  # noqa: S310 (127.0.0.1 only)
            body = resp.read().decode("utf-8", "replace")
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        return None, f"{type(exc).__name__}: {exc}"
    try:
        data = json.loads(body)
    except ValueError:
        return None, "non-JSON response"
    if not isinstance(data, dict):
        return None, "response is not a JSON object"
    return data, None


def _find_item_in_tracks(data: dict, item_id: str) -> dict | None:
    """The item dict with this id, from a `build_snapshot`-shaped `{'tracks': [{'items': [...]},
    ...]}` response — or `None` if no track carries it."""
    for tr in data.get("tracks") or []:
        if not isinstance(tr, dict):
            continue
        for it in tr.get("items") or []:
            if isinstance(it, dict) and it.get("id") == item_id:
                return it
    return None


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
