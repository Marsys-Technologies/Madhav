"""Suvarṇa independent-review bundle builder (launch item L.12r).

    python -m suvarna_tracker.review_bundle --out DIR [--zip] [--force]
        [--plan-root DIR] [--nikasha-root DIR] [--madhav-root DIR] [--home DIR]

Assembles, for the independent third-party reviewer (L.9; read-only sandbox, no database,
no credentials, no network), one folder holding the Suvarṇa v1.4.x plan set and everything it
leans on. Every file is placed at its repository path under ``DIR`` (the sources are all branches
or checkouts of the one Madhav repository, so their repo-relative paths do not collide; a
collision aborts). The decisions-log snapshot, which lives outside git, goes to ``run/``.

It writes two generated files:

* ``MANIFEST.txt`` — one tab-separated row per file: bundle path, source path, the git commit of
  the source checkout, whether the file differs from that commit (``clean`` / ``modified`` /
  ``untracked`` / ``not-in-git``), and its sha256. Superseded plan versions are listed by name
  only (not copied).
* ``README_FIRST.md`` — points to the review package.

**Secrets.** Every source file is scanned *before* anything is copied. Any hit (connection URL
with a password, ``PGPASSWORD=`` with a value, a quoted ``password`` of 8+ characters, a
private-key header, AWS/GCP key shapes, a long base64-like run next to "key"/"secret"/"token")
aborts the build with exit 3, listing ``file:line: pattern``, and nothing is written. Placeholders
(``$VAR``, ``<...>``) and the exact fixture values in ``KNOWN_FIXTURE_VALUES`` are the only
exemptions; hex digests, paths and snake_case identifiers are not base64 runs.

Exit codes: 0 built · 2 refused (bad arguments, missing source, existing output, path collision)
· 3 secret found.
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime as _dt
import hashlib
import math
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

PACKAGE_REL = "00_ARCHITECTURE/briefs/suvarna/SUVARNA_REVIEW_PACKAGE_v1_0.md"
SUVARNA_BRIEFS = "00_ARCHITECTURE/briefs/suvarna"
TRACKER_REL = "platform/scripts/governance/suvarna_tracker"

DEFAULT_PLAN_ROOT = str(Path(__file__).resolve().parents[4])
DEFAULT_NIKASHA_ROOT = "/Users/Dev/madhav-nikasha"
DEFAULT_MADHAV_ROOT = "/Users/Dev/Vibe-Coding/Apps/Madhav"
DEFAULT_HOME = "/Users/Dev/suvarna"

# Directory walks never copy these.
EXCLUDED_DIR_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".git",
                      "node_modules"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
EXCLUDED_NAMES = {".DS_Store"}


class BundleError(Exception):
    """A refusal (exit 2)."""


class SecretFound(Exception):
    """One or more secret-pattern hits (exit 3). ``hits`` is a list of (source, line, pattern)."""

    def __init__(self, hits: list[tuple[str, int, str]]):
        self.hits = hits
        super().__init__(f"{len(hits)} secret-pattern hit(s)")


@dataclasses.dataclass(frozen=True)
class Entry:
    rel: str      # path inside the bundle
    src: Path     # absolute source path


@dataclasses.dataclass(frozen=True)
class Roots:
    plan: Path
    nikasha: Path
    madhav: Path
    home: Path


# --------------------------------------------------------------------------------------------
# Sources
# --------------------------------------------------------------------------------------------

def _walk(root: Path, rel_dir: str) -> list[Entry]:
    base = root / rel_dir
    if not base.is_dir():
        raise BundleError(f"missing source folder: {base}")
    out: list[Entry] = []
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDED_DIR_NAMES)
        for name in sorted(filenames):
            if name in EXCLUDED_NAMES or Path(name).suffix in EXCLUDED_SUFFIXES:
                continue
            p = Path(dirpath) / name
            out.append(Entry(p.relative_to(root).as_posix(), p))
    return out


def _file(root: Path, rel: str, bundle_rel: str | None = None) -> Entry:
    return Entry(bundle_rel or rel, root / rel)


def default_entries(roots: Roots) -> list[Entry]:
    """The L.12r bundle contents, in reading order."""
    b = SUVARNA_BRIEFS
    p = roots.plan
    entries = [
        _file(p, PACKAGE_REL),
        _file(p, f"{b}/SUVARNA_CAMPAIGN_PLAN_v1_4.md"),
        _file(p, f"{b}/SUVARNA_AUTONOMY_CHARTER_v1_0.md"),
        _file(p, f"{b}/SUVARNA_EXECUTION_ARCHITECTURE_v1_0.md"),
        _file(p, f"{b}/SUVARNA_RUNBOOK_v1_0.md"),
        _file(p, f"{b}/D6_SUVARNA_READER_RUNBOOK_v1_0.md"),
        _file(p, f"{b}/SUVARNA_L3_FOCUS_FAMILIES_v1_0.md"),
        _file(p, f"{b}/SUVARNA_DOCUMENT_MAP_v1_0.md"),
    ]
    for sub in ("tracks", "roles", "prompts", "runtime", "reviews", "l3_recon"):
        entries += _walk(p, f"{b}/{sub}")
    entries.append(_file(p, "00_ARCHITECTURE/control/suvarna/plan_model.json"))
    entries += _walk(p, TRACKER_REL)
    entries.append(_file(p, "platform/scripts/suvarna-reader-bootstrap.ts"))
    entries.append(_file(roots.nikasha, "00_ARCHITECTURE/briefs/nirmana/NIKASHA_CHANGE_REGISTER_v2_0.md"))
    entries.append(_file(roots.nikasha, "00_ARCHITECTURE/briefs/nirmana/NIKASHA_IMPLEMENTATION_PLAN_v1_0.md"))
    entries.append(_file(roots.madhav, "CLAUDE.md"))
    entries.append(_file(roots.home, "run/DECISIONS.jsonl", "run/DECISIONS.jsonl"))
    return entries


def superseded_entries(roots: Roots) -> list[Entry]:
    """Listed in the manifest by name only; never copied."""
    return [_file(roots.plan, f"{SUVARNA_BRIEFS}/SUVARNA_CAMPAIGN_PLAN_v1_{n}.md") for n in range(4)]


# --------------------------------------------------------------------------------------------
# Secret scan
# --------------------------------------------------------------------------------------------

# Values that are placeholders or shell references, never secrets.
_PLACEHOLDER_RE = re.compile(r"^(?:\$\{?\w+\}?|\$\(.*|<[^>]*>|\.{3}|…|\*+|x+|X+)$")
# Well-known fixture passwords used by the tracker's own tests (e.g. test_monitor.py's
# `postgres://user:hunter2@…` sanitiser fixture). Exact values only, listed here so the exemption
# is auditable; any other value is a hit.
KNOWN_FIXTURE_VALUES = frozenset({"hunter2", "changeme", "redacted", "REDACTED"})

_VALUE_PATTERNS = {"connection-url-with-password", "PGPASSWORD-with-value", "quoted-password"}

_SIMPLE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("connection-url-with-password",
     re.compile(r"postgres(?:ql)?://[^\s:/@'\"]+:([^\s@/'\"]+)@", re.IGNORECASE)),
    ("PGPASSWORD-with-value",
     re.compile(r"PGPASSWORD\s*=\s*['\"]?([^\s'\"`;&|)]{4,})")),
    ("quoted-password",
     re.compile(r"password['\"]?\s*[:=]\s*(['\"])([^'\"\s]{8,})\1", re.IGNORECASE)),
    ("private-key-header",
     re.compile(r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY(?: BLOCK)?-----")),
    ("aws-access-key-id", re.compile(r"\b(?:AKIA|ASIA|AGPA|AIDA|AROA)[0-9A-Z]{16}\b")),
    ("aws-secret-access-key",
     re.compile(r"aws_?secret_?access_?key\w*['\"]?\s*[:=]\s*['\"]?[A-Za-z0-9/+=]{40}", re.IGNORECASE)),
    ("gcp-api-key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("gcp-service-account-key", re.compile(r"\"private_key\"\s*:\s*\"-----BEGIN")),
]

_B64_RUN_RE = re.compile(r"[A-Za-z0-9+/_\-]{40,}={0,2}")
_KEYWORD_RE = re.compile(r"key|secret|token", re.IGNORECASE)
_HEX_RE = re.compile(r"^[0-9a-fA-F]+$")
_KEYWORD_WINDOW = 32
_MIN_ENTROPY = 4.2


def _entropy(s: str) -> float:
    counts: dict[str, int] = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1
    n = len(s)
    return -sum(c / n * math.log2(c / n) for c in counts.values())


_MIN_SEGMENT = 20


def _looks_like_b64_secret(run: str) -> bool:
    core = run.rstrip("=")
    if _HEX_RE.match(core):
        return False  # git SHAs and sha256 digests
    if not (re.search(r"[0-9]", core) and re.search(r"[A-Z]", core) and re.search(r"[a-z]", core)):
        return False
    # Paths and snake/kebab identifiers (`00_ARCHITECTURE/control/registry_coverage_report`) break
    # into short segments; 40+ random base64 characters almost never do.
    if max(len(s) for s in re.split(r"[/+_\-]", core)) < _MIN_SEGMENT:
        return False
    return _entropy(core) >= _MIN_ENTROPY


def scan_text(text: str) -> list[tuple[int, str]]:
    """Return (line number, pattern name) for every secret-pattern hit in ``text``."""
    hits: list[tuple[int, str]] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for name, rx in _SIMPLE_PATTERNS:
            for m in rx.finditer(line):
                value = m.group(m.lastindex) if m.lastindex else m.group(0)
                if name in _VALUE_PATTERNS and (_PLACEHOLDER_RE.match(value)
                                                or value in KNOWN_FIXTURE_VALUES):
                    continue
                hits.append((lineno, name))
                break
        for m in _B64_RUN_RE.finditer(line):
            if not _looks_like_b64_secret(m.group(0)):
                continue
            window = line[max(0, m.start() - _KEYWORD_WINDOW):m.start()] + \
                line[m.end():m.end() + _KEYWORD_WINDOW]
            if _KEYWORD_RE.search(window):
                hits.append((lineno, "base64-run-near-key/secret/token"))
                break
    return hits


def scan_entries(entries: list[Entry]) -> list[tuple[str, int, str]]:
    hits: list[tuple[str, int, str]] = []
    for e in entries:
        text = e.src.read_bytes().decode("utf-8", errors="replace")
        hits += [(str(e.src), ln, name) for ln, name in scan_text(text)]
    return hits


# --------------------------------------------------------------------------------------------
# Git provenance
# --------------------------------------------------------------------------------------------

class _GitInfo:
    def __init__(self) -> None:
        self._top: dict[Path, str | None] = {}
        self._head: dict[str, str] = {}

    def _run(self, cwd: Path | str, *args: str) -> str | None:
        try:
            r = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True,
                               timeout=30)
        except (OSError, subprocess.TimeoutExpired):
            return None
        return r.stdout.strip() if r.returncode == 0 else None

    def describe(self, src: Path) -> tuple[str, str]:
        """(commit, state) for a source file; ('-', 'not-in-git') outside any repository."""
        d = src.parent
        if d not in self._top:
            self._top[d] = self._run(d, "rev-parse", "--show-toplevel")
        top = self._top[d]
        if not top:
            return "-", "not-in-git"
        if top not in self._head:
            self._head[top] = self._run(top, "rev-parse", "HEAD") or "-"
        rel = os.path.relpath(src.resolve(), Path(top).resolve())
        porcelain = self._run(top, "status", "--porcelain", "--untracked-files=all", "--", rel)
        if porcelain is None:
            state = "unknown"
        elif porcelain == "":
            state = "clean"
        elif porcelain.startswith("??"):
            state = "untracked"
        elif porcelain.startswith("!!"):
            state = "ignored"
        else:
            state = "modified"
        return self._head[top], state


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------------------------

README_TEXT = """# Suvarṇa — independent review bundle

Start here: **`{package}`** (the review package). It says what is under review, what is being
decided, the reading order, the questions, and the report format we need from you.

- Every file sits at its repository path. The decisions log (kept outside git) is at
  `run/DECISIONS.jsonl`, a snapshot taken when the bundle was built.
- `MANIFEST.txt` lists every file with its source path, the git commit of its source checkout,
  whether it differed from that commit when copied, and its sha256. Superseded plan versions are
  named there but not included.
- The bundle was scanned for secrets before it was built; it holds no credentials, and you need
  none: no database, network or tool access is expected.

Built {built} by `python -m suvarna_tracker.review_bundle`.
"""


def _check_collisions(entries: list[Entry]) -> None:
    seen: dict[str, Path] = {}
    for e in entries:
        if e.rel in ("MANIFEST.txt", "README_FIRST.md"):
            raise BundleError(f"source maps onto a generated file name: {e.src}")
        if e.rel in seen and seen[e.rel].resolve() != e.src.resolve():
            raise BundleError(f"bundle path collision at {e.rel}: {seen[e.rel]} and {e.src}")
        seen[e.rel] = e.src


def _dedupe(entries: list[Entry]) -> list[Entry]:
    out, seen = [], set()
    for e in entries:
        if e.rel not in seen:
            seen.add(e.rel)
            out.append(e)
    return out


def build_bundle(out_dir: str | Path, entries: list[Entry], superseded: list[Entry] | None = None,
                 make_zip: bool = False, force: bool = False,
                 package_rel: str = PACKAGE_REL) -> dict:
    """Scan, then copy ``entries`` into ``out_dir`` and write MANIFEST.txt and README_FIRST.md.

    Raises BundleError (refusal) or SecretFound (scan hit); in both cases nothing is written."""
    out = Path(out_dir).expanduser().resolve()
    superseded = superseded or []

    missing = [str(e.src) for e in entries if not e.src.is_file()]
    if missing:
        raise BundleError("missing source file(s):\n  " + "\n  ".join(missing))
    _check_collisions(entries)
    entries = _dedupe(entries)
    if package_rel not in {e.rel for e in entries}:
        raise BundleError(f"the review package {package_rel} is not in the bundle")

    hits = scan_entries(entries)
    if hits:
        raise SecretFound(hits)

    if out.exists():
        if not force and (not out.is_dir() or any(out.iterdir())):
            raise BundleError(f"output exists and is not empty: {out} (use --force to replace it)")
        if out.is_dir():
            shutil.rmtree(out)
        else:
            out.unlink()
    zip_path = out.with_name(out.name + ".zip")
    if make_zip and zip_path.exists() and not force:
        raise BundleError(f"zip exists: {zip_path} (use --force to replace it)")

    git = _GitInfo()
    rows = []
    out.mkdir(parents=True)
    for e in entries:
        dest = out / e.rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(e.src, dest)  # content + permission bits (hold_guard.sh must stay executable)
        commit, state = git.describe(e.src)
        digest = sha256_file(dest)
        if digest != sha256_file(e.src):
            raise BundleError(f"source changed while copying: {e.src}")
        rows.append((e.rel, str(e.src), commit, state, digest))

    built = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "# Suvarṇa independent review bundle — manifest",
        f"# built: {built}",
        f"# files: {len(rows)} (plus this manifest and README_FIRST.md)",
        "# columns: bundle_path<TAB>source_path<TAB>source_git_commit<TAB>git_state<TAB>sha256",
        "# git_state: clean = identical to that commit; modified/untracked = working-tree copy; "
        "not-in-git = outside any repository",
        "",
    ]
    lines += ["\t".join(r) for r in rows]
    if superseded:
        lines += ["", "# Superseded — named only, NOT included in the bundle:"]
        for s in superseded:
            commit, state = git.describe(s.src) if s.src.is_file() else ("-", "absent")
            digest = sha256_file(s.src) if s.src.is_file() else "-"
            lines.append("\t".join(("NOT-INCLUDED:" + s.rel, str(s.src), commit, state, digest)))
    (out / "MANIFEST.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "README_FIRST.md").write_text(README_TEXT.format(package=package_rel, built=built),
                                         encoding="utf-8")

    generated_hits = scan_entries([Entry("MANIFEST.txt", out / "MANIFEST.txt"),
                                   Entry("README_FIRST.md", out / "README_FIRST.md")])
    if generated_hits:
        shutil.rmtree(out)
        raise SecretFound(generated_hits)

    result = {"out": str(out), "files": len(rows), "zip": None}
    if make_zip:
        if zip_path.exists():
            zip_path.unlink()
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path in sorted(p for p in out.rglob("*") if p.is_file()):
                zf.write(path, arcname=f"{out.name}/{path.relative_to(out).as_posix()}")
        result["zip"] = str(zip_path)
    return result


# --------------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Build the Suvarṇa independent-review bundle (L.12r)")
    ap.add_argument("--out", required=True, help="output folder (must not exist, or be empty)")
    ap.add_argument("--zip", action="store_true", help="also write <out>.zip")
    ap.add_argument("--force", action="store_true", help="replace an existing output folder/zip")
    ap.add_argument("--plan-root", default=DEFAULT_PLAN_ROOT,
                    help="checkout of strategy/suvarna-plan (default: this file's repository)")
    ap.add_argument("--nikasha-root", default=DEFAULT_NIKASHA_ROOT)
    ap.add_argument("--madhav-root", default=DEFAULT_MADHAV_ROOT,
                    help="checkout whose CLAUDE.md is bundled")
    ap.add_argument("--home", default=os.environ.get("SUVARNA_HOME", DEFAULT_HOME),
                    help="SUVARNA_HOME (the decisions log is run/DECISIONS.jsonl under it)")
    return ap


def main(argv: list[str] | None = None) -> int:
    a = build_arg_parser().parse_args(argv)
    roots = Roots(Path(a.plan_root), Path(a.nikasha_root), Path(a.madhav_root), Path(a.home))
    try:
        result = build_bundle(a.out, default_entries(roots), superseded_entries(roots),
                              make_zip=a.zip, force=a.force)
    except SecretFound as exc:
        print("ABORTED: possible secret(s) found; nothing was written:", file=sys.stderr)
        for src, line, name in exc.hits:
            print(f"  {src}:{line}: {name}", file=sys.stderr)
        return 3
    except BundleError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    print(f"bundle: {result['out']} ({result['files']} files + MANIFEST.txt, README_FIRST.md)")
    if result["zip"]:
        print(f"zip: {result['zip']}")
    return 0


if __name__ == "__main__":
    if __package__ in (None, ""):
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.exit(main())
