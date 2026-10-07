"""build_window.py -- the Build.history window (SS definition, binding), read-only and fail-closed.

Build.history judges the attempts SINCE the later of

  (i)  the asset's last WRITER-DIGEST change on main, and
  (ii) its last REGISTRY-IDENTITY change (depends_on, integrity_check_sql, count_sql, has_substeps, scope, ...),

because an earlier error belongs to code or to a contract that no longer exists. This module answers only the two
"when" questions, from git, with no database and no network. The grading itself (what a window reads) lives in
asset_census.py (`_grade_build_history_windowed`); this file is the dating.

WHAT "LAST CHANGE" READS
  (i) CODE. The engine's writer digest (`asset_runner.get_writer_source_hash`) is a content hash over the writer's
      source roots plus the transitive closure of the local imports it follows. The census reproduces that SET of
      files (asset_census._writer_code_paths) and this module dates it: the committer time (`%ct`, UTC epoch) of the
      newest commit reachable from the `main` ref that touches any file of the set (`git log -1 -- <files>`).
      A commit that touches a file without changing its bytes (a rename, a mode change, a no-op revert) still moves
      the date: that can only make the window start LATER, so the reading errs toward NO_DETECTOR, never toward PASS.
  (ii) REGISTRY IDENTITY. The registry is database state with no change timestamp, so the repo-readable record is
      read instead: the newest commit on the `main` ref touching any file under `platform/migrations` or
      `platform/scripts/seed` that names BOTH `asset_registry` and the asset id (whole-word match). This is an
      over-approximation by design (a migration that names the asset for a description or a grant also counts):
      again later only, never earlier.

HOW IT FAILS CLOSED (every one is `ok=False` with a reason that the cell quotes; never a window, never PASS)
  * git is missing or a call fails or times out;
  * the repository is a shallow clone (the last-change date would be the graft date, not the truth);
  * neither `origin/main` nor `main` resolves (an explicit `ref` is tried alone);
  * the working tree differs from the ref in the dated files (the code under judgment is not the code on main);
  * a dated file is not tracked at the ref, or no commit at the ref touches the set;
  * NO migration or seed row on main names the asset (its registry identity cannot be dated);
  * the code path set is empty.

RESIDUALS (stated, not hidden; see the Build.history criterion text and the report)
  * Deploy lag: a commit's time is when the change landed on main, not when it was deployed or applied. An attempt
    between landing and deploy ran the OLD code or contract yet reads as "since". The engine's per-attempt receipt
    (`asset_provenance_receipts.code_digest`, keyed by build id) is the exact instrument; it is not read here.
  * A registry change made by hand, or by a bulk statement that names no asset id, is not seen.
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

WINDOW_SCHEMA = "build_history_window/1"
MAIN_REFS = ("origin/main", "main")
MIGRATION_PATHS = ("platform/migrations", "platform/supabase/migrations")
SEED_FILE = "platform/scripts/seed/asset_registry_seed.ts"
_GIT_TIMEOUT = 30
_REGISTRY_STMT = re.compile(r"\b(?:INSERT\s+INTO|UPDATE)\s+(?:public\.)?asset_registry\b", re.I)


class WindowUnknown(Exception):
    """The window cannot be determined; the message is the reason the cell quotes."""


def _scrubbed_env() -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return env


def _split_top(text: str) -> list[str]:
    """Split on the commas of `text` that are outside quotes and parentheses."""
    out, depth, cur, q, i = [], 0, [], None, 0
    while i < len(text):
        ch = text[i]
        if q:
            cur.append(ch)
            if ch == q:
                if i + 1 < len(text) and text[i + 1] == q:
                    cur.append(text[i + 1])
                    i += 1
                else:
                    q = None
        elif ch in "'\"":
            q = ch
            cur.append(ch)
        elif ch == "(":
            depth += 1
            cur.append(ch)
        elif ch == ")":
            depth -= 1
            cur.append(ch)
        elif ch == "," and depth == 0:
            out.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
        i += 1
    out.append("".join(cur).strip())
    return out


def _balanced_groups(text: str) -> list[str]:
    """The top-level parenthesised groups of `text` (contents without the outer parentheses), quotes respected."""
    out, depth, start, q = [], 0, None, None
    for i, ch in enumerate(text):
        if q:
            if ch == q:
                q = None
        elif ch in "'\"":
            q = ch
        elif ch == "(":
            if depth == 0:
                start = i + 1
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0 and start is not None:
                out.append(text[start:i])
    return out


_FALSE_LIT = re.compile(r"^(?:false|'f'|'false'|'n'|'no'|0)$", re.I)


def _sets_has_writer_false(stmt: str, asset_id: str) -> bool:
    """True when one `INSERT INTO asset_registry` / `UPDATE asset_registry` statement that names the asset sets `has_writer` to false for it: an UPDATE `SET ... has_writer = false`, or an
    INSERT whose column list names has_writer and whose VALUES row for the asset (the group that holds the id as a quoted string) has a false literal at that position. A statement the reader
    cannot map (no column list, a value that is not a literal) is NOT counted: the caller then dates the row by its creation, the stricter reading."""
    if re.match(r"\s*UPDATE", stmt, re.I):
        # only the SET clause assigns: `SET has_writer = true WHERE ... AND has_writer = false` must not count (the WHERE is a predicate). The SET list runs to the first top-level WHERE / FROM / RETURNING.
        m = re.search(r"\bSET\b(.*?)(?=\bWHERE\b|\bFROM\b|\bRETURNING\b|$)", stmt, re.I | re.S)
        if not m:
            return False
        return any(re.fullmatch(r"has_writer\s*=\s*(?:false|'f'|'false')", a.strip(), re.I) is not None for a in _split_top(m.group(1)))
    m = re.match(r"\s*INSERT\s+INTO\s+(?:public\.)?asset_registry\s*\(([^)]*)\)\s*VALUES\s*(.*)$", stmt, re.I | re.S)
    if not m:
        return False
    cols = [c.strip().strip('"').lower() for c in m.group(1).split(",")]
    if "has_writer" not in cols:
        return False
    idx = cols.index("has_writer")
    for g in _balanced_groups(m.group(2)):
        vals = _split_top(g)
        if len(vals) == len(cols) and any(v.strip("'\"") == asset_id for v in vals):
            return bool(_FALSE_LIT.match(vals[idx].strip()))
    return False



class WindowReader:
    """Read-only git reader for one repository. Never writes, never fetches, never touches the network."""

    def __init__(self, repo: Path, ref: str | None = None, env: dict | None = None):
        self.repo = Path(repo)
        self._ref_arg = ref
        self._env = env if env is not None else _scrubbed_env()
        self._sha: str | None = None
        self._ref_name: str | None = None
        self._ref_error: str | None = None
        self._resolved = False
        self._seed_lines: list[str] | None = None

    def _git(self, *args: str, ok_codes=(0,)) -> subprocess.CompletedProcess:
        try:
            p = subprocess.run(["git", *args], capture_output=True, text=True, timeout=_GIT_TIMEOUT,
                               env=self._env, cwd=str(self.repo), shell=False)
        except (OSError, subprocess.SubprocessError) as exc:
            raise WindowUnknown(f"git could not run ({type(exc).__name__})") from exc
        if p.returncode not in ok_codes:
            tail = ((p.stderr or "").strip().splitlines() or ["no output"])[-1][:160]
            raise WindowUnknown(f"git {args[0]} failed (exit {p.returncode}): {tail}")
        return p

    def resolve(self) -> tuple[str, str]:
        """(ref name, commit sha) of main, once. Raises WindowUnknown (cached) when it cannot be certified."""
        if not self._resolved:
            self._resolved = True
            try:
                if self._git("rev-parse", "--is-shallow-repository").stdout.strip() != "false":
                    raise WindowUnknown("the repository is a shallow clone: the last-change date would be the graft date, "
                                        "not the truth")
                cands = (self._ref_arg,) if self._ref_arg else MAIN_REFS
                for c in cands:
                    p = self._git("rev-parse", "--verify", "--quiet", f"{c}^{{commit}}", ok_codes=(0, 1))
                    sha = p.stdout.strip()
                    if p.returncode == 0 and len(sha) in (40, 64):
                        self._sha, self._ref_name = sha, c
                        break
                else:
                    raise WindowUnknown(f"none of {', '.join(cands)} resolves to a commit in this checkout")
            except WindowUnknown as exc:
                self._ref_error = str(exc)
        if self._ref_error:
            raise WindowUnknown(self._ref_error)
        return self._ref_name, self._sha          # type: ignore[return-value]

    def last_commit(self, paths: list[str]) -> tuple[int, str] | None:
        """(committer epoch, sha) of the newest commit reachable from the ref touching any of `paths`; None when none does."""
        _name, sha = self.resolve()
        p = self._git("log", "-1", "--format=%ct%x09%H", sha, "--", *paths)
        out = p.stdout.strip()
        if not out:
            return None
        ct, _, h = out.partition("\t")
        try:
            return int(ct), h
        except ValueError as exc:
            raise WindowUnknown(f"git log answered an unreadable commit time {ct!r}") from exc

    def tracked_and_unmodified(self, paths: list[str]) -> None:
        """Every path is a file at the ref and the working tree holds exactly the ref's bytes for it."""
        _name, sha = self.resolve()
        listed = {x for x in self._git("ls-tree", "-r", "--name-only", sha, "--", *paths).stdout.splitlines() if x}
        missing = sorted(set(paths) - listed)
        if missing:
            raise WindowUnknown(f"writer file(s) not tracked at the main ref: {', '.join(missing[:3])}")
        if self._git("diff", "--quiet", sha, "--", *paths, ok_codes=(0, 1)).returncode == 1:
            raise WindowUnknown("the working tree differs from the main ref in the writer files: the code under judgment "
                                "is not the code on main")

    def _seed_row_commit(self, asset_id: str) -> tuple[int, str] | None:
        """Newest commit that changed the asset's OWN row in the registry seed (its `{ ... asset_id: '<id>', ... },` object literal), by line-range
        history (`git log -L`): the seed names every asset, so a file-level date would move every window whenever any row is edited. None when
        the seed holds no such row."""
        _name, sha = self.resolve()
        if self._seed_lines is None:                 # read once per reader: the seed is 3.7k lines and every asset asks
            p = self._git("show", f"{sha}:{SEED_FILE}", ok_codes=(0, 128))
            self._seed_lines = p.stdout.split("\n") if p.returncode == 0 else []
        lines = self._seed_lines
        needle = f"asset_id: '{asset_id}',"
        hits = [i for i, ln in enumerate(lines) if ln.strip() == needle]
        if not hits:
            return None
        if len(hits) > 1:
            raise WindowUnknown(f"the registry seed holds {len(hits)} rows for {asset_id}: its row span is ambiguous")
        k = hits[0]
        start = k                                    # 0-based index of the line after the opening `{` (1-based line k = the `{`)
        end = next((i for i in range(k + 1, len(lines)) if lines[i].startswith("  }")), None)
        if end is None:
            raise WindowUnknown(f"the registry seed row of {asset_id} has no closing brace")
        out = self._git("log", "-1", "--format=%ct%x09%H", "-s", f"-L{start},{end + 1}:{SEED_FILE}", sha).stdout.strip()
        if not out:
            return None
        ct, _, h = out.partition("\t")
        try:
            return int(ct), h
        except ValueError as exc:
            raise WindowUnknown(f"git log -L answered an unreadable commit time {ct!r}") from exc

    def _registry_statements(self, sha: str, path: str, asset_id: str) -> list[str]:
        """The `INSERT INTO asset_registry ...` / `UPDATE asset_registry ...` statements of one migration (at `sha`) that name `asset_id` as a whole word. A statement runs from its keyword to
        the next `;` (a conservative reading: a `;` inside a string literal ends it early, which can only lose a mention, never invent one). A file that merely MENTIONS the id (a comment, a
        grant, a SELECT, a statement about another table) has none."""
        txt = self._git("show", f"{sha}:{path}", ok_codes=(0, 128)).stdout
        word = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(asset_id) + r"(?![A-Za-z0-9_])")
        out = []
        for m in _REGISTRY_STMT.finditer(txt):
            end = txt.find(";", m.end())
            stmt = txt[m.start(): end if end >= 0 else len(txt)]
            if word.search(stmt):
                out.append(stmt)
        return out

    def _registry_statement_files(self, asset_id: str, need_has_writer: bool = False) -> list[str]:
        _name, sha = self.resolve()
        p = self._git("grep", "-l", "--all-match", "-F", "-w", "-e", "asset_registry", "-e", asset_id, sha, "--", *MIGRATION_PATHS, ok_codes=(0, 1))
        files = sorted({ln.split(":", 1)[1] for ln in p.stdout.splitlines() if ":" in ln})
        keep = []
        for f in files:
            sts = self._registry_statements(sha, f, asset_id)
            if sts and (not need_has_writer or any(re.search(r"\bhas_writer\b", st, re.I) for st in sts)):
                keep.append(f)
        return keep

    def has_writer_commit(self, asset_id: str) -> tuple[int, str, str] | None:
        """(epoch, sha, basis) of the instant the asset BECAME writer-less (SS 2026-10-05 R-c), or None when it cannot be dated (the caller fails closed).
          basis `migration set has_writer = false`: the NEWEST migration (platform/migrations) with an INSERT / UPDATE asset_registry statement naming the id that sets has_writer to false, dated by
              the commit that ADDED the statement on main (`git log -S<id>`: a later unrelated touch of the file does not move it). The ledger's `applied_at` of that migration is a production
              value this reader cannot see: the commit date on main is a LABELLED PROXY for it, and the cell's evidence says so. A seed-file `has_writer:` line is not a migration and never sets it;
          basis `created writer-less`: no migration ever set it, so the row was created writer-less (the column default is false: a service row): the EARLIEST commit that created the row (an INSERT
              statement in a migration, or the first commit of its seed row). Any build attempt later than that contradicts "never had a writer"."""
        _name, sha = self.resolve()
        sets = []
        for f in self._registry_statement_files(asset_id, need_has_writer=True):
            if not any(_sets_has_writer_false(st, asset_id) for st in self._registry_statements(sha, f, asset_id)):
                continue
            out = self._git("log", "-1", "--format=%ct%x09%H", "-S" + asset_id, sha, "--", f).stdout.strip()
            if out:
                ct, _, h = out.partition("\t")
                sets.append((int(ct), h))
        if sets:
            e, h = max(sets)
            return e, h, "migration set has_writer = false"
        made = []
        for f in self._registry_statement_files(asset_id):
            if any(re.match(r"\s*INSERT", st, re.I) for st in self._registry_statements(sha, f, asset_id)):
                out = self._git("log", "--reverse", "--format=%ct%x09%H", "-S" + asset_id, sha, "--", f).stdout.strip().splitlines()
                if out:
                    ct, _, h = out[0].partition("\t")
                    made.append((int(ct), h))
        span = self._seed_span(asset_id, sha)
        if span is not None:
            blocks = self._git("log", "--format=@@@%ct%x09%H", "-s", f"-L{span[0]},{span[1]}:{SEED_FILE}", sha).stdout.split("@@@")[1:]
            if blocks:
                ct, _, h = blocks[-1].partition("\n")[0].partition("\t")
                made.append((int(ct), h.strip()))
        if made:
            e, h = min(made)
            return e, h, "created writer-less"
        return None

    def commit_epoch(self, sha: str) -> int | None:
        """The committer time of commit `sha` (must be a full or abbreviated object id in this checkout), None when the checkout does not hold it."""
        p = self._git("show", "-s", "--format=%ct", sha, ok_codes=(0, 128))
        txt = p.stdout.strip()
        return int(txt) if p.returncode == 0 and txt.isdigit() else None

    def file_at_main(self, path: str) -> str | None:
        """The text of `path` at the main ref, or None when the file does not exist there."""
        _name, sha = self.resolve()
        p = self._git("show", f"{sha}:{path}", ok_codes=(0, 128))
        return p.stdout if p.returncode == 0 else None

    def _seed_span(self, asset_id: str, sha: str):
        if self._seed_lines is None:
            p = self._git("show", f"{sha}:{SEED_FILE}", ok_codes=(0, 128))
            self._seed_lines = p.stdout.split("\n") if p.returncode == 0 else []
        lines = self._seed_lines
        hits = [i for i, ln in enumerate(lines) if ln.strip() == f"asset_id: '{asset_id}',"]
        if not hits:
            return None
        if len(hits) > 1:
            raise WindowUnknown(f"the registry seed holds {len(hits)} rows for {asset_id}: its row span is ambiguous")
        end = next((i for i in range(hits[0] + 1, len(lines)) if lines[i].startswith("  }")), None)
        if end is None:
            raise WindowUnknown(f"the registry seed row of {asset_id} has no closing brace")
        return hits[0], end + 1

    def registry_commit(self, asset_id: str) -> tuple[int, str] | None:
        """Newest of (a) the newest commit touching a migration file that names `asset_registry` AND `asset_id` (whole word), and (b) the
        newest commit that changed the asset's own row in the registry seed. None when neither exists."""
        _name, sha = self.resolve()
        found = []
        p = self._git("grep", "-l", "--all-match", "-F", "-w", "-e", "asset_registry", "-e", asset_id, sha, "--",
                      *MIGRATION_PATHS, ok_codes=(0, 1))
        files = sorted({ln.split(":", 1)[1] for ln in p.stdout.splitlines() if ":" in ln})
        if files:
            c = self.last_commit(files)
            if c:
                found.append(c)
        c = self._seed_row_commit(asset_id)
        if c:
            found.append(c)
        return max(found) if found else None


def _iso(epoch: float) -> str:
    import datetime as dt
    return dt.datetime.fromtimestamp(epoch, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def compute_window(reader: WindowReader, asset_id: str, code_paths: list[str]) -> dict:
    """The window start for one asset: `dict(ok=True, epoch, basis, ...)` or `dict(ok=False, reason)`. Never raises."""
    try:
        if not code_paths:
            raise WindowUnknown("the writer's source files are unknown (no code path set)")
        ref, sha = reader.resolve()
        paths = sorted(set(code_paths))
        reader.tracked_and_unmodified(paths)
        code = reader.last_commit(paths)
        if code is None:
            raise WindowUnknown(f"no commit on {ref} touches the writer's source files, so the last writer-digest change "
                                "cannot be dated")
        reg = reader.registry_commit(asset_id)
        if reg is None:
            raise WindowUnknown(f"no migration or seed on {ref} names {asset_id} against asset_registry, so its registry "
                                "identity cannot be dated")
    except WindowUnknown as exc:
        return dict(ok=False, reason=str(exc))
    epoch = max(code[0], reg[0])
    later = "writer digest" if code[0] >= reg[0] else "registry identity"
    basis = (f"writer source ({len(paths)} file(s)) last changed {_iso(code[0])} in {code[1][:9]}; registry identity last "
             f"named {_iso(reg[0])} in {reg[1][:9]}; window opens at the later ({later}) on {ref} {sha[:9]}")
    return dict(ok=True, epoch=float(epoch), code_epoch=code[0], code_sha=code[1], registry_epoch=reg[0],
                registry_sha=reg[1], ref=ref, ref_sha=sha, files=len(paths), basis=basis, opens=_iso(epoch),
                schema=WINDOW_SCHEMA)
