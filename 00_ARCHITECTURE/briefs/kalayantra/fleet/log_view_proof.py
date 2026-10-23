#!/usr/bin/env python3
"""Step-10 POSITIVE log-view proof (surrogate ruling 2026-10-22 09:2xZ; root CLAUDE.md §N.8) — stdlib only, no gcloud, no network, no credential.

What it measures.  The seal workflow's brief job reads the verification job's logs THROUGH the single-job log view
`projects/madhav-astrology/locations/global/buckets/_Default/views/gochara_verification_job`, under its own github-actions@ identity (this program never impersonates and never
calls gcloud: it is handed the `gcloud logging read --format=json` exports the workflow already holds).  Two claims, each a detector that can read FALSE:
  view_returns_job_entries  the view returns at least one entry of `gochara-verification-job` (resource.type = cloud_run_job, resource.labels.job_name = the job): an empty or unreadable view proves nothing
  view_only_job_entries     EVERY returned entry has resource.type = cloud_run_job AND job_name = `gochara-verification-job`: one entry of any other resource makes it false
and one claim it deliberately does NOT measure:
  view_refusal_outside      = NULL, always.  Whether the view REFUSES entries outside the job needs the project-wide `roles/logging.viewer` narrowed (SR-LOGVIEW-NARROW-KEEP keeps it; the
                            LOGVIEW-NARROW-IAC item re-evaluates).  There is no detector behind it, so it is null, never green (§N.8; §N.7.6).
Two sources are checked, each on its own: `probe` (a bounded read through the view with NO resource filter, so a foreign entry could appear in it) and `execution` (the existing
per-execution read the brief is extracted from; its query already filters, so it can only prove the positive side).  The controller re-measures the same groups on every poll rather than
trusting the recorded verdict.  The retained document carries (type, job_name, count) groups only — never a log payload.

CLI:  log_view_proof.py check --probe-file F --execution-logs-file G --run-id N --attempt N --execution NAME --out PATH     exit 0 PROVEN / 2 HOLD (named reason on stderr)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCHEMA = "ky.log_view_proof/1"
JOB = "gochara-verification-job"
RESOURCE_TYPE = "cloud_run_job"
VIEW = "projects/madhav-astrology/locations/global/buckets/_Default/views/gochara_verification_job"
SOURCES = ("probe", "execution")
POSITIVE, ONLY_JOB, OUTSIDE = "view_returns_job_entries", "view_only_job_entries", "view_refusal_outside"
OUTSIDE_REASON = "project-wide logging.viewer kept by SR-LOGVIEW-NARROW-KEEP; re-evaluated by LOGVIEW-NARROW-IAC"
_NAME = re.compile(r"[A-Za-z0-9._-]{1,200}")


class ViewUnreadable(Exception):
    """The export is not a JSON array of log entries (or the document is malformed): the view was not read, so nothing is proven."""


def groups_of(entries) -> list[dict]:
    """Collapse a `gcloud logging read --format=json` export into (type, job_name, count) groups.  An entry that is not an object, or has no resource, falls in the (None, None) group."""
    if not isinstance(entries, list):
        raise ViewUnreadable("the log export is not a JSON array of entries")
    counts: dict[tuple, int] = {}
    for e in entries:
        res = e.get("resource") if isinstance(e, dict) else None
        labels = res.get("labels") if isinstance(res, dict) else None
        typ = res.get("type") if isinstance(res, dict) else None
        job = labels.get("job_name") if isinstance(labels, dict) else None
        key = (typ if isinstance(typ, str) else None, job if isinstance(job, str) else None)
        counts[key] = counts.get(key, 0) + 1
    return [{"type": t, "job_name": j, "count": n} for (t, j), n in sorted(counts.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1])))]


def _checked_groups(groups) -> list[dict]:
    if not isinstance(groups, list):
        raise ViewUnreadable("groups is not a list")
    for g in groups:
        if not (isinstance(g, dict) and set(g) == {"type", "job_name", "count"} and isinstance(g["count"], int) and not isinstance(g["count"], bool) and g["count"] >= 1
                and all(g[k] is None or isinstance(g[k], str) for k in ("type", "job_name"))):
            raise ViewUnreadable("a group is malformed")
    return groups


def rows_of(groups) -> list[dict]:
    """The two detector rows for ONE source (the outside-refusal row has no detector, so it is not a per-source row: see `outside_row`)."""
    groups = _checked_groups(groups)
    job = [g for g in groups if g["type"] == RESOURCE_TYPE and g["job_name"] == JOB]
    foreign = [g for g in groups if not (g["type"] == RESOURCE_TYPE and g["job_name"] == JOB)]
    n_job, n_foreign = sum(g["count"] for g in job), sum(g["count"] for g in foreign)
    total = n_job + n_foreign
    if total == 0:
        why_pos = "the view returned no entries at all: an empty view proves nothing"
    elif n_job == 0:
        why_pos = f"none of the {total} returned entries is an entry of {JOB}"
    else:
        why_pos = f"{n_job} of {total} returned entries are of {JOB}"
    if n_foreign:
        shown = ", ".join(f"{g['count']}x type={g['type']!r} job_name={g['job_name']!r}" for g in foreign[:5])
        why_only = f"{n_foreign} of {total} returned entries are NOT of {RESOURCE_TYPE}/{JOB} ({shown})"
    else:
        why_only = f"all {total} returned entries are of {RESOURCE_TYPE}/{JOB}" if total else "no entries returned: nothing outside the job (vacuous; the positive row decides)"
    return [{"check": POSITIVE, "result": n_job > 0, "reason": why_pos},
            {"check": ONLY_JOB, "result": n_foreign == 0, "reason": why_only}]


def outside_row() -> dict:
    """`view_refusal_outside`: NO detector exists behind it, so it is NULL — never True — whatever the other rows say (§N.8, §N.7.6)."""
    return {"check": OUTSIDE, "result": None, "reason": OUTSIDE_REASON}


def combine(per_source: dict[str, list[dict]]) -> list[dict]:
    """One row per check across every source: True only if EVERY source is True; the first false reason is named with its source; the outside row stays None."""
    out = []
    for check in (POSITIVE, ONLY_JOB):
        rows = {s: next(r for r in per_source[s] if r["check"] == check) for s in SOURCES}
        bad = [f"{s}: {r['reason']}" for s, r in rows.items() if r["result"] is not True]
        out.append({"check": check, "result": not bad, "reason": "; ".join(bad) if bad else "; ".join(f"{s}: {r['reason']}" for s, r in rows.items())})
    out.append(outside_row())
    return out


def passed(rows: list[dict]) -> bool:
    return all(r["result"] is True for r in rows if r["check"] in (POSITIVE, ONLY_JOB))


def build(exports: dict, *, run_id: int, attempt: int, execution: str) -> dict:
    """The retained proof document from the two exports ({source: parsed JSON array})."""
    per, srcs = {}, {}
    for s in SOURCES:
        g = groups_of(exports[s])
        srcs[s] = {"groups": g}
        per[s] = rows_of(g)
    rows = combine(per)
    return {"schema": SCHEMA, "view": VIEW, "job": JOB, "run_id": run_id, "attempt": attempt, "execution": execution, "sources": srcs, "rows": rows, "passed": passed(rows)}


def verify(doc, *, run_id: int, attempt: int) -> dict:
    """Re-measure a retained document (the controller's call).  Raises ViewUnreadable for a malformed / mismatched / self-contradicting document; otherwise returns
    {"passed": bool, "rows": [...], "reason": <named reason when not passed>}.  The recorded rows and verdict are never trusted: they must equal what the groups give."""
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA:
        raise ViewUnreadable(f"the proof is not a {SCHEMA} document")
    if doc.get("view") != VIEW or doc.get("job") != JOB:
        raise ViewUnreadable("the proof names another view or job")
    if (doc.get("run_id"), doc.get("attempt")) != (run_id, attempt):
        raise ViewUnreadable(f"the proof is of run {doc.get('run_id')!r} attempt {doc.get('attempt')!r}, not the brief run {run_id} attempt {attempt}")
    srcs = doc.get("sources")
    if not isinstance(srcs, dict) or set(srcs) != set(SOURCES) or not all(isinstance(srcs[s], dict) and "groups" in srcs[s] for s in SOURCES):
        raise ViewUnreadable(f"the proof lacks one of its sources {SOURCES}")
    rows = combine({s: rows_of(srcs[s]["groups"]) for s in SOURCES})
    if doc.get("rows") != rows:
        raise ViewUnreadable("the recorded rows differ from the rows the recorded groups give (altered or forged proof)")
    if doc.get("passed") is not passed(rows):
        raise ViewUnreadable("the recorded verdict differs from the verdict the rows give")
    reason = "" if passed(rows) else "; ".join(f"{r['check']}: {r['reason']}" for r in rows if r["result"] is False)
    return {"passed": passed(rows), "rows": rows, "reason": reason}


def _load(path: str, what: str):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ViewUnreadable(f"{what} is not readable JSON ({path}): {exc}") from None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("--probe-file", required=True)
    c.add_argument("--execution-logs-file", required=True)
    c.add_argument("--run-id", type=int, required=True)
    c.add_argument("--attempt", type=int, required=True)
    c.add_argument("--execution", required=True)
    c.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    try:
        if not _NAME.fullmatch(a.execution):
            raise ViewUnreadable("the execution name has unsafe characters")
        doc = build({"probe": _load(a.probe_file, "the unfiltered view read"), "execution": _load(a.execution_logs_file, "the per-execution view read")},
                    run_id=a.run_id, attempt=a.attempt, execution=a.execution)
    except ViewUnreadable as exc:
        print(f"::error::HOLD positive_log_view_proof: unreadable — {exc}", file=sys.stderr)
        return 2
    Path(a.out).write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    for r in doc["rows"]:
        print(f"{r['check']}: {r['result']}  ({r['reason']})")
    if not doc["passed"]:
        print("::error::HOLD positive_log_view_proof: " + "; ".join(f"{r['check']}: {r['reason']}" for r in doc["rows"] if r["result"] is False), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
