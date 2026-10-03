#!/usr/bin/env python3
"""ledger_e6_4_info_rekey.py -- Suvarna E6.4 (SS N-97(4)): re-key the non-gate criteria (Cost, Count, Complete, Reach)
of the delta ledger `00_ARCHITECTURE/control/asset_gaps.jsonl` from open `kind: gap` rows to `kind: info`, by a reviewed,
idempotent, append-only migration (the R81 pattern of ledger_r81_migration.py).

WHY A NEW ID. The E6.3 reader fixes a gap's (kind, criterion) at its first write: a later `kind: info` row under the SAME
gap_id raises ("may not change to kind 'info'"). So for every eligible row O (gap_id G) this appends
  1. a NEW row under `G#info`: kind `info`, the same asset / criterion / what / change / detector / owner / gate / state
     (the measurement evidence is carried VERBATIM), plus `rekeyed_from: G` and `rekey` (the ruling),
  2. a copy of O's latest row with `superseded_by: G#info` (R81's superseding row; O is never edited or deleted).
`emit_gaps_summary` never resurrects a superseded id (`ever_superseded`), never measures a `#info` id (a measured gap id is
`<asset>-<criterion>` and a criterion has no `#`), and (E6.4, asset_census.INFO_ONLY_GATES) no longer opens a gap on these
families at all. A static snapshot (N-97(4)): the info rows are not updated by later censuses.

ELIGIBLE (and only this): the LATEST row of a gap_id with kind gap (or absent), state OPEN / IN_PROGRESS / RE-OPENED, a
criterion starting `Cost.` / `Count.` / `Complete.` / `Reach.` (so Completeness.* and Reachability* are not matched), whose id
was never superseded. CLOSED / WITHDRAWN rows, opportunity / info rows, every gate criterion and line 1 (`_schema`) are
untouched; the old file's bytes are an exact prefix of the new one. A second run finds nothing eligible and writes nothing.

Usage (a COPY first; the canonical ledger only after review):
  ledger_e6_4_info_rekey.py --src COPY --dst COPY2 [--dry-run] [--ts ISO]
  ledger_e6_4_info_rekey.py --src <canonical> --dst <canonical> --ts ISO       # in place: appends only the new lines
The canonical ledger path (nikasha_fold.GAPS_REL of a git work tree) as --dst requires --src to be the SAME file and
nikasha_fold.git_preflight to pass (tracked, HEAD bytes a prefix, no uncommitted change, E4.3 cut-over landed).
Also refused: a --ts that is not timezone-aware; a --dst that is hard-linked (st_nlink > 1) or shares an inode with the
canonical ledger; a different EXISTING --dst whose bytes are neither --src's nor the planned output (never silently
overwritten); an in-place run while another holds the census lock (SUVARNA_CENSUS_LOCK or --lock-file; exit 75).
Provenance: migration-written rows keep the census detector/owner/gate of the row they re-key; they are marked by `rekey`
(and `rekeyed_from` on the info row), `superseded_by` on the superseding copy, and ts = the migration ts.

APPLY RUNBOOK (after review, never before):
  1. Run the governance suite on the MIGRATED COPY committed in a scratch repo BEFORE committing the apply: the six
     ledger-reading files (test_r15_r29_hand_row_census_run_id, test_r80_schema_superseded_by_field, test_r81_apply_script,
     test_r81_ledger_overlap_fold, test_e4_3_cutover, test_e5_2_fold) + test_e6_3_* + test_e6_4_info_rekey.
     (test_e6_4_info_rekey.py::test_ledger_reading_suite_on_the_migrated_real_ledger does this offline for the ledger-readers
     that accept a ledger path; the rest need the file in a checkout.)
  2. Dry run: --dry-run (expect 219 rekeyed = Cost.baseline 123, Complete.depth 57, Count.floor 39, Reach 0, +438 lines).
  3. Apply in place (clean tracked ledger, E4.3 cut-over landed), then commit the one file; a second run writes nothing.
E6.4 supersedes R81 group 8's rule for the four info prefixes: bg_panchanga-Cost.baseline is now superseded BY its E6.4
`#info` id (its other census sibling, Earn.build_record, is untouched).
Exit: 0 ok (also "nothing to do") - 2 refused (stderr `REFUSED <code>: ...`, nothing written) - 5 script error - 75 lock held.
"""
from __future__ import annotations

import argparse
import collections
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
import sys
import stat
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nikasha_fold as nf  # noqa: E402  (ONE definition of the canonical-ledger path and its git preconditions)

INFO_PREFIXES = tuple(g + "." for g in nf.ac.INFO_ONLY_GATES)     # ONE definition (asset_census.INFO_ONLY_GATES) == the plan detector's criteria_prefixes
LIVE_STATES = frozenset({"OPEN", "IN_PROGRESS", "RE-OPENED"})       # emit's live states + the detector's RE-OPENED
INFO_SUFFIX = "#info"
RULING = "E6.4 / SS N-97(4): non-gate family re-keyed to kind info (static census snapshot)"
EX_REFUSED, EX_ERROR = 2, 5


class RekeyRefused(nf.FoldRefused):
    """Refused; nothing was written (same type family as the fold's refusals, `code` is the stable slug)."""


def _refuse(code: str, message: str):
    raise RekeyRefused(code, message)


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _is_target(r: dict) -> bool:
    return isinstance(r.get("criterion"), str) and r["criterion"].startswith(INFO_PREFIXES)


def _is_live_gap(r: dict) -> bool:
    return (str(r.get("kind", "gap")).lower() == "gap" and str(r.get("state", "OPEN")).upper() in LIVE_STATES)


def info_id(gap_id: str) -> str:
    return gap_id + INFO_SUFFIX


def parse_ledger(data: bytes) -> list:
    """Every line as a dict (line 1 is the `_schema` row). Refuses a ledger that is not valid UTF-8 JSON-lines of objects,
    has no trailing newline (an append would glue onto the last line) or whose first line is not the `_schema` row."""
    if data and not data.endswith(b"\n"):
        _refuse("ledger_no_trailing_newline", "the ledger's last line is unterminated: an append would glue onto it")
    rows = []
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as e:
        _refuse("ledger_not_utf8", str(e))
    for n, ln in enumerate(text.split("\n")[:-1] if text else [], 1):
        if not ln.strip():
            continue
        try:
            r = json.loads(ln)
        except json.JSONDecodeError:
            _refuse("ledger_line_invalid", f"line {n} is not JSON")
        if not isinstance(r, dict):
            _refuse("ledger_line_invalid", f"line {n} is not a JSON object")
        rows.append(r)
    if not rows or rows[0].get("asset") != "_schema":
        _refuse("ledger_no_schema_row", "line 1 is not the _schema row")
    return rows


def _latest(rows: list) -> tuple:
    """Same convention as emit_gaps / the tracker: last row in FILE order wins per gap_id; `superseded_by` is permanent."""
    latest, ever_sup = {}, set()
    for r in rows[1:]:
        gid = r.get("gap_id")
        if gid:
            latest[gid] = r
            if r.get("superseded_by"):
                ever_sup.add(gid)
    return latest, ever_sup


def detector_open(rows: list, prefixes=INFO_PREFIXES) -> list:
    """The plan detector's own check (suvarna_tracker/detectors.py ledger_state + d_ledger_no_open_gap_on): latest row per gap_id,
    state OPEN / RE-OPENED, kind gap (absent = gap), no `superseded_by` on that latest row, criterion startswith the prefixes."""
    last = {}
    for d in rows:
        if d.get("asset") == "_schema" or "gap_id" not in d:
            continue
        last[d["gap_id"]] = d
    return [d for d in last.values() if d.get("state") in ("OPEN", "RE-OPENED") and d.get("kind", "gap") == "gap"
            and not d.get("superseded_by") and str(d.get("criterion", "")).startswith(tuple(prefixes))]


def eligible(rows: list) -> list:
    """The latest rows to re-key, in ledger order of their latest row. Refuses a live eligible row without a gap_id."""
    latest, ever_sup = _latest(rows)
    out = []
    for r in rows[1:]:
        if r.get("gap_id"):
            continue
        if _is_target(r) and _is_live_gap(r):
            _refuse("unfoldable_row", f"a live {r.get('criterion')!r} row of {r.get('asset')!r} has no gap_id: it cannot be superseded")
    for gid, r in latest.items():
        if gid in ever_sup or not _is_target(r) or not _is_live_gap(r):
            continue
        out.append(r)
    return out


def fold_info_rekeys(rows: list, ts: str) -> list:
    """The NEW rows to APPEND (never mutates `rows`): for each eligible row, the `<id>#info` row then the superseding copy.
    Pure; idempotent (a second call on its own output is empty). Refuses on a collision: the new id already exists."""
    latest, _ = _latest(rows)
    new, seen_new = [], set()
    for old in eligible(rows):
        gid = old["gap_id"]
        nid = info_id(gid)
        if nid in latest or nid in seen_new:
            _refuse("info_id_collision", f"the new id {nid!r} already exists in the ledger while {gid!r} is not superseded: "
                                         "an inconsistent partial state, resolve by review")
        seen_new.add(nid)
        info = dict(old)
        info.pop("superseded_by", None)
        info.update(gap_id=nid, kind="info", ts=ts, rekeyed_from=gid, rekey=RULING)
        sup = dict(old)
        sup.update(superseded_by=nid, ts=ts)
        new.extend([info, sup])
    return new


def dump_rows(rows: list) -> bytes:
    return b"".join(json.dumps(r, ensure_ascii=False).encode("utf-8") + b"\n" for r in rows)


def check_result(old_rows: list, new_rows: list) -> None:
    """Postconditions, checked BEFORE anything is written. Refuses (nothing written) on any failure. They are written from
    the ledger's own fields, NOT through `_is_target` / `_is_live_gap`: a defect in the eligibility rule must not blind them."""
    on_target = lambda r: str(r.get("criterion") or "").startswith(("Cost.", "Count.", "Complete.", "Reach."))
    is_live = lambda r: str(r.get("kind", "gap")).lower() == "gap" and str(r.get("state", "OPEN")).upper() in ("OPEN", "IN_PROGRESS", "RE-OPENED")
    allrows = old_rows + new_rows
    if detector_open(allrows):
        _refuse("detector_still_open", f"{len(detector_open(allrows))} open gap row(s) remain on {INFO_PREFIXES} after the migration")
    latest, ever_sup = _latest(allrows)
    first = {}
    for r in allrows[1:]:
        g = r.get("gap_id")
        if g:
            f = first.setdefault((r.get("asset"), g), (r.get("kind", "gap"), r.get("criterion", "")))
            if f != (r.get("kind", "gap"), r.get("criterion", "")):
                _refuse("identity_changed", f"{g!r} of {r.get('asset')!r} would change its (kind, criterion): the reader raises")
    for r in new_rows:
        g, sup = r.get("gap_id"), r.get("superseded_by")
        if sup:
            t = latest.get(sup)
            if t is None or t.get("asset") != r.get("asset") or t.get("kind") != "info" or t.get("rekeyed_from") != g:
                _refuse("dangling_supersede", f"{g!r} is superseded by {sup!r}, which is not its own same-asset info row")
    ids = [r["gap_id"] for r in new_rows if r.get("kind") == "info"]
    if len(ids) != len(set(ids)):
        _refuse("info_id_collision", "two new rows share one info id")
    if len([r for r in new_rows if r.get("superseded_by")]) != len(ids):
        _refuse("unbalanced_rekey", "every info row needs exactly one superseding row")
    for r in new_rows:
        if r.get("kind") == "info" and not on_target(r):
            _refuse("gate_criterion_touched", f"{r.get('criterion')!r} is not a Cost/Count/Complete/Reach criterion")
    old_latest, old_sup = _latest(old_rows)
    for r in new_rows:
        if r.get("superseded_by"):
            o = old_latest.get(r["gap_id"])
            if o is None or r["gap_id"] in old_sup or not is_live(o):
                _refuse("closed_row_touched", f"{r['gap_id']!r} is not a live, never-superseded gap row: only those are re-keyed")
            if not on_target(o):
                _refuse("gate_criterion_touched", f"{o.get('criterion')!r} is not a Cost/Count/Complete/Reach criterion")
    # evidence: every info row carries the old row's `what`, detector and criterion verbatim
    by_id = {r["gap_id"]: r for r in old_rows[1:] if r.get("gap_id")}
    for r in new_rows:
        if r.get("kind") == "info":
            o = by_id.get(r["rekeyed_from"])
            if o is None or any(r.get(k) != o.get(k) for k in ("asset", "criterion", "what", "detector", "change", "owner", "gate", "state")):
                _refuse("evidence_dropped", f"{r['gap_id']!r} does not carry the measurement evidence of {r['rekeyed_from']!r}")


def plan(src_bytes: bytes, ts: str) -> dict:
    """Pure: the migration of `src_bytes`. Returns dict(new_rows, new_bytes, counts, out_bytes)."""
    old_rows = parse_ledger(src_bytes)
    new_rows = fold_info_rekeys(old_rows, ts)
    check_result(old_rows, new_rows)
    by_crit = collections.Counter(r["criterion"] for r in new_rows if r.get("kind") == "info")
    by_prefix = {p: sum(n for c, n in by_crit.items() if c.startswith(p)) for p in INFO_PREFIXES}
    nb = dump_rows(new_rows)
    return dict(new_rows=new_rows, new_bytes=nb, out_bytes=src_bytes + nb, by_criterion=dict(sorted(by_crit.items())),
                by_prefix=by_prefix, open_before=len(detector_open(old_rows)),
                open_after=len(detector_open(old_rows + new_rows)), rows_before=len(old_rows))


def _atomic_write(path: Path, data: bytes, mode: int | None = None) -> None:
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".e64tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            if mode is not None:
                os.fchmod(f.fileno(), mode)
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def _append(path: Path, orig: bytes, new: bytes) -> None:
    fd = os.open(str(path), os.O_RDWR | os.O_APPEND)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        if path.read_bytes() != orig:
            _refuse("ledger_changed_during_migration", "the ledger changed between reading and appending: re-run")
        try:
            view = memoryview(new)
            while len(view):
                n = os.write(fd, view)
                if n <= 0:
                    raise OSError("short write")
                view = view[n:]
            os.fsync(fd)
        except OSError as e:
            os.ftruncate(fd, len(orig))
            _refuse("ledger_write_failed", f"the append failed ({e}); the ledger was restored")
    finally:
        with contextlib.suppress(OSError):
            fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _is_canonical(path: Path) -> bool:
    info = nf.canonical_info(path)
    return bool(info and info["canonical"])


def _canonical_candidates() -> list:
    """The canonical ledger paths this run could be aliasing: this script's repo's and the current directory's repo's."""
    cands = [nf.repo_root() / nf.GAPS_REL]
    top = nf.git_top(Path.cwd())
    if top is not None:
        cands.append(top / nf.GAPS_REL)
    return cands


def aliases_canonical(path: Path) -> bool:
    """True when `path` is a DIFFERENT name for the inode of a canonical ledger (a hard link: realpath-based checks cannot see it).
    The same file under its own (real) path is not an alias; that case is `_is_canonical`'s."""
    if _is_canonical(path):
        return False
    try:
        st, me = os.stat(path), os.path.realpath(path)
    except OSError:
        return False
    for c in _canonical_candidates():
        with contextlib.suppress(OSError):
            cs = os.stat(c)
            if (cs.st_dev, cs.st_ino) == (st.st_dev, st.st_ino) and os.path.realpath(c) != me:
                return True
    return False


def _require_tz_aware(ts: str) -> None:
    try:
        t = dt.datetime.fromisoformat(ts)
    except (TypeError, ValueError):
        _refuse("bad_ts", f"--ts {ts!r} is not an ISO timestamp")
    if t.tzinfo is None or t.utcoffset() is None:
        _refuse("bad_ts", f"--ts {ts!r} is not timezone-aware (the ledger's timestamps carry an offset)")


def run(src, dst, *, ts: str, dry_run: bool = False, lock_file=None) -> dict:
    """Migrate `src` into `dst` (src == dst: in place, appending only the new lines). Returns a report dict."""
    _require_tz_aware(ts)
    sp, dp = Path(src), Path(dst)
    if not sp.is_file() or sp.is_symlink():
        _refuse("src_missing", f"{sp} is not a regular file")
    if dp.is_symlink() or dp.is_dir():
        _refuse("dst_invalid", f"{dp} is a symlink or a directory")
    if not dp.parent.is_dir():
        _refuse("dst_dir_missing", f"{dp.parent} is not a directory")
    with nf.census_lock(None if dry_run else lock_file):
        return _run_locked(sp, dp, ts=ts, dry_run=dry_run)


def _run_locked(sp: Path, dp: Path, *, ts: str, dry_run: bool) -> dict:
    same = dp.exists() and os.path.realpath(sp) == os.path.realpath(dp)
    orig = sp.read_bytes()
    pl = plan(orig, ts)
    canonical = _is_canonical(dp) or _is_canonical(sp)
    writing = bool(pl["new_rows"]) and not dry_run
    if writing and dp.exists():
        if aliases_canonical(dp) or (dp.stat().st_nlink > 1):
            _refuse("dst_hardlinked", f"{dp} is hard-linked (or an alias of the canonical ledger's inode): a write through it would "
                                       "bypass the canonical-ledger protections; use a plain file")
    # the canonical ledger: only in place, only after the fold's own git preconditions (ONE definition, nikasha_fold). Nothing to do
    # writes nothing, so it needs no precondition (a second run on an already-migrated, not yet committed ledger is a clean no-op).
    if canonical and writing:
        if not same:
            _refuse("canonical_path", "the canonical ledger is migrated in place only (--src == --dst): it is never the --dst of "
                                       "a different --src (that would overwrite it) nor the --src of a different --dst")
        nf.git_preflight(dp, allow_dirty=False, dry_run=False)
    if writing and dp.exists() and not same and dp.read_bytes() not in (orig, pl["out_bytes"]):
        _refuse("dst_exists_different", f"{dp} exists and is neither the source nor the planned output: it is not silently overwritten")
    rep = dict(src=str(sp), dst=str(dp), dry_run=dry_run, in_place=same, ts=ts, rows_before=pl["rows_before"],
               sha256_before=_sha(orig), open_gaps_before=pl["open_before"], open_gaps_after=pl["open_after"],
               rekeyed=len(pl["new_rows"]) // 2, by_criterion=pl["by_criterion"], by_prefix=pl["by_prefix"],
               appended_lines=len(pl["new_rows"]))
    if not pl["new_rows"]:
        rep.update(status="unchanged", sha256_after=_sha(orig))
        return rep                                  # nothing to do: nothing is written, not even --dst
    if dry_run:
        rep.update(status="dry_run", sha256_after=_sha(pl["out_bytes"]))
        return rep
    if not pl["out_bytes"].startswith(orig):
        _refuse("not_append_only", "internal: the new bytes do not extend the old ones")
    if same:
        _append(dp, orig, pl["new_bytes"])
    else:
        mode = stat.S_IMODE((dp if dp.exists() else sp).stat().st_mode)           # keep the file's mode (a new copy takes the source's)
        _atomic_write(dp, pl["out_bytes"], mode)
    rep.update(status="migrated", sha256_after=_sha(dp.read_bytes()))
    return rep


def _parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--src", required=True, help="ledger to read (a COPY, or the canonical ledger for an in-place run)")
    ap.add_argument("--dst", required=True, help="ledger to write (== --src for in place)")
    ap.add_argument("--dry-run", action="store_true", help="report only; write nothing")
    ap.add_argument("--ts", default=None, help="the migration timestamp (ISO, tz-aware); default now")
    ap.add_argument("--lock-file", default=None, help=f"census lock file (default: ${nf.ENV_LOCK}); exit 75 when held")
    return ap


def main(argv=None) -> int:
    a = _parser().parse_args(argv)
    ts = a.ts or dt.datetime.now().astimezone().isoformat(timespec="seconds")
    try:
        rep = run(a.src, a.dst, ts=ts, dry_run=a.dry_run, lock_file=a.lock_file or os.environ.get(nf.ENV_LOCK))
    except nf.FoldRefused as e:
        print(f"REFUSED {e.code}: {e.message}", file=sys.stderr)
        return EX_REFUSED
    except nf.LockHeld as e:
        print(f"LOCK HELD: {e}", file=sys.stderr)
        return nf.EX_TEMPFAIL
    except Exception as e:  # noqa: BLE001 - one stderr line, like the fold
        print(f"ERROR {type(e).__name__}: {e}"[:300], file=sys.stderr)
        return EX_ERROR
    print(json.dumps(rep, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
