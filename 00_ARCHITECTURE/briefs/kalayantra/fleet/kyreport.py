#!/usr/bin/env python3
"""kyreport.py — the measured status report of KĀLA-YANTRA v3 (relaunch plan v2.7 §13 "Measurement"; packet
KV3-B-KYREPORT, rulings P14 and P15). version: 1.1 · status: DRAFT — pending independent review.

    kyreport.py [--today] [--events E] [--model M]      one JSON report on stdout (P15: the status report of the
                                                        cockpit prompt's step 4; `--today` is its alias)
    kyreport.py approval --expect X                     platform approval, read back from GitHub; exit 0 only
                                                        when `verified`
    kyreport.py baseline-import --repo G --commit C --path P --review-receipt V --dest D
                                                        install the reviewed token baseline from the object store

Exit: 0 a report · 1 approval not verified / import refused · 64 usage · 66 $KY_RUN missing.

The report launches nothing, admits nothing and writes nothing: it reads $KY_RUN, asks the read-only helpers
beside this file (`kyloop.py admin show|child`, `kyveto.py status`, `kyqualify.py check`, `kygate.sh
--pre-resume`) and, only when a session has no result event and the baseline is verified, runs the installed
baseline script. `kyloop.py admin …` and `kyveto.py status` are asked through their own `main(argv)`, loaded from
the file beside this one into this process (their output is what the command prints; `python3 -B` would otherwise
compile kyloop.py again for every question; `admin expected-qualification` reads the pinned binary's
`--version`, as kyloop.py itself does — no model is called). The two files it must hand to another program (a launch
configuration for `kyqualify.py check`, the baseline's `--json OUT`) are made in a private temporary directory
and removed again.

WHAT A FIGURE IS. {"value", "denominator", "observed"} — or {"value": "unknown", "why", …}. `unknown` is never 0,
false or a green word; a measured empty set is `[]` / `{}` with its denominator. `observed` is the report's
observation boundary: {events_path, events_lines, prefix_sha256, from, to} of the complete lines of the event log
that were read. Savings and throughput are `cannot_be_estimated` (§13).

completions   E (default $KY_RUN/EVENTS.jsonl) and M (default $PRAVAHA_PLAN_MODEL) through the tracker's
              `state.build_snapshot` ($KY_TRACKER_LIVE, default $KY_ROOT/tracker_live), with no detector results:
              guarded-completed item ids, decision completions, joins, accepted heads and weighted progress are
              separate figures, each with its own scope denominator.
jobs          $KY_RUN/jobs/*/state.json (KV3-B-KYDJOBS); a missing field is `unknown`.
tokens        the four `usage` classes kyprobe.py reads from a stream `result` event. Every provider session has
              ONE owner: a job state (`provider_session_id`, `result_event`) or a role state
              ($KY_RUN/PLANNER_STATE.json, CONDUCTOR_STATE.json: exactly one session identity, else `unknown`).
              The same session with an identical result payload is a duplicate and counts once; with two different
              payloads it is not added. A session without a result event (a killed job, an interactive planner or
              conductor) is counted only from the verified baseline. A child session (`parent_session_id`) is
              added only if the baseline receipt's `parent_includes_children` is exactly false, left out when it
              is exactly true AND the parent it names (parent_session_id, or parent_job_id's session) is a
              session counted in this report, and uncovered otherwise. A total exists only while the baseline is verified and
              every session is covered; otherwise it is `unknown` and what was measured is labelled `partial`.
signals       each from the source the packet names, else `unknown`:
              loop_healthy        STOPPED · HEALTHY · UNHEALTHY · unknown (see loop_health)
              loop_progress       the loop's last judged run (`progressed`) and `no_progress_count`
              probe_pass          `kyqualify.py check … --require-context launchd --verify-evidence`
              surrogate_decision  the state `kyveto.py status` gives it; veto_expired: the handler's own record
              owner_notified      `notification.submitted` AND the `[notify=submitted]` journal line
              platform_approval   only `kyreport.py approval --expect X` can say `verified`
              WAVE_B_DONE         the marker, re-bound to the final receipt and the manifest as they are now
              READY_TO_START      `kygate.sh --pre-resume`

BASELINE (P14). `baseline-import` takes blob C:P from the object store of G and nothing from a work tree; C is a
full commit id. The review receipt V must say {verdict "ACCEPTED", reviewer_session_id ≠ author_session_id,
source_commit C, inputs[P] = the blob's sha256}. Under one kyaction record it writes D and
$KY_RUN/BASELINE_RECEIPT.json {source_commit, path, sha256, review_receipt_sha256, installed_path,
parent_includes_children: null}; any refusal exits 1 with its reason and writes nothing. The baseline is
`verified_installed` only while that receipt is readable and `installed_path` hashes to `sha256`. The one adapter
is `python3 -B <installed_path> --json OUT` (keys sources, grand_total, by_role, top_sessions).

Changelog
  1.0 (2026-10-12)  first version (KV3-B-KYREPORT).
  1.1 (2026-10-12)  review round 1, B-01: a child is left out as inside its parent only when that parent resolves
                    to a session counted here, else it is uncovered; no counted session → the total is unknown,
                    and per_guarded_completion cannot raise.
"""
from __future__ import annotations

import collections
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

FLEET = Path(__file__).resolve().parent
sys.dont_write_bytecode = True                  # a report writes nothing, a helper's cache file included
sys.path.insert(0, str(FLEET))
import kyaction  # noqa: E402

SCHEMA = "ky.report/1"
UNKNOWN = "unknown"
CANNOT = "cannot_be_estimated"
CLASSES = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")
BASELINE_CLASSES = {"input": "input_tokens", "cache_creation": "cache_creation_input_tokens",
                    "cache_read": "cache_read_input_tokens", "output": "output_tokens"}
BASELINE_KEYS = ("sources", "grand_total", "by_role", "top_sessions")
JOB_KEYS = ("job_id", "item", "kind", "role", "phase", "provider_session_id", "result_event")   # pinned (KYDJOBS)
LOOPS = ("planner", "conductor", "veto")        # every loop kyloop.py is the controller of
PROBE_ROLES = ("planner", "conductor")          # the roles that launch model jobs
ROLE_STATES = (("planner", "PLANNER_STATE.json"), ("conductor", "CONDUCTOR_STATE.json"))
ITERATION_MAX_AGE_S = 120.0                     # INTERPRETATION: 4 × kyloop's longest poll (HOLD_POLL_S = 30 s)
CLOCK_SLACK_S = 5.0                             # how far ahead of this clock a recorded iteration may be
HELPER_TIMEOUT_S = 60.0
GATE_TIMEOUT_S = 330.0                          # kygate.sh --pre-resume may run kyversion.sh for up to 300 s
BASELINE_TIMEOUT_S = 900.0
HEX40, HEX64 = re.compile(r"^[0-9a-f]{40}\Z"), re.compile(r"^[0-9a-f]{64}\Z")
REPO_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9._-]+\Z")
NOTIFY_LINE = re.compile(r"^- (\S+) \[[a-z_]+\] (.*) \[notify=(submitted|failed|dry)\]\s*\Z")    # as kyveto.py
CHILD_STATES = ("none", "pending", "alive", "survivors", "gone", "unknown")
DECISION_STATES = ("PROPOSED", "PENDING_VETO", "EFFECTIVE", "EXECUTED", "VETOED", "FAILED")
USAGE = ("usage: kyreport.py [--today] [--events E] [--model M]\n"
         "       kyreport.py approval --expect X\n"
         "       kyreport.py baseline-import --repo G --commit C --path P --review-receipt V --dest D")


# ───────────────────────────────────── small things ─────────────────────────────────────

def is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def text(v):
    return v if isinstance(v, str) and v.strip() else None


def fig(value, denominator, observed, **more):
    return dict({"value": value, "denominator": denominator, "observed": observed}, **more)


def unknown(why, denominator, observed, **more):
    return dict({"value": UNKNOWN, "why": why, "denominator": denominator, "observed": observed}, **more)


def scope(name, count):
    return {"scope": name, "count": count if is_int(count) else UNKNOWN}


def signal(value, source, why=None, **more):
    out = {"value": value, "source": source}
    if why:
        out["why"] = why
    out.update(more)
    return out


def run_dir(environ):
    return Path(environ.get("KY_RUN") or Path(environ.get("KY_ROOT") or "/Users/Dev/kalayantra") / "run")


def helper(argv, run, timeout=HELPER_TIMEOUT_S):
    """(exit code, stdout, stderr) of a read-only helper, or (None, "", reason) when it could not be run."""
    try:
        r = subprocess.run([str(a) for a in argv], capture_output=True, text=True, timeout=timeout,
                           stdin=subprocess.DEVNULL, env=dict(os.environ, KY_RUN=str(run)))
    except (OSError, subprocess.SubprocessError, ValueError) as e:
        return None, "", type(e).__name__
    return r.returncode, r.stdout, r.stderr


def py(script, *args):
    return [sys.executable, "-B", str(FLEET / script)] + list(args)


def private_tmp():
    return tempfile.mkdtemp(prefix="kyreport.", dir=os.environ.get("TMPDIR") or None)


_LOADED = {}


def ask(script, argv, run):
    """(exit code, stdout, "") of `<script> <argv…>` beside this file, by calling its main(argv) in this process;
    (None, "", reason) when it cannot be loaded or raises. Only the read-only questions named in the module
    docstring are ever asked this way. The module is loaded under a private name, once per file content."""
    path = FLEET / script
    try:
        key = (str(path), kyaction.sha_file(path))
        module = _LOADED.get(key)
        if module is None:
            spec = importlib.util.spec_from_file_location("kyreport_helper_" + path.stem, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            _LOADED[key] = module
        out, saved = io.StringIO(), os.environ.get("KY_RUN")
        os.environ["KY_RUN"] = str(run)
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                rc = module.main([str(a) for a in argv])
        except SystemExit as e:
            rc = e.code if is_int(e.code) else 0 if e.code is None else 1
        finally:
            if saved is None:
                os.environ.pop("KY_RUN", None)
            else:
                os.environ["KY_RUN"] = saved
    except Exception as e:      # noqa: BLE001 — a helper that cannot answer makes its signal unknown, never a crash
        return None, "", type(e).__name__
    return (rc if is_int(rc) else None), out.getvalue(), ""


def parse_object(out):
    try:
        doc = json.loads(out)
    except (ValueError, RecursionError):
        return None
    return doc if isinstance(doc, dict) else None


# ───────────────────────────────────── the observation boundary ─────────────────────────────────────

def read_events(path):
    """(events | None, observed, problem | None). Only complete lines are read; the prefix that was read is hashed.
    A line that is not a JSON object is a missing record: no figure is computed from such a log."""
    observed = {"events_path": str(path), "events_lines": None, "prefix_sha256": None, "from": None, "to": None}
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except FileNotFoundError:
        return None, observed, "the event log %s is missing" % path
    except OSError as e:
        return None, observed, "the event log %s cannot be read (%s)" % (path, type(e).__name__)
    prefix = raw[:raw.rfind(b"\n") + 1]
    lines = prefix.split(b"\n")[:-1]
    observed.update(events_lines=len(lines), prefix_sha256=hashlib.sha256(prefix).hexdigest())
    events, bad = [], 0
    for line in lines:
        if not line.strip():
            continue
        try:
            ev = json.loads(line.decode("utf-8"))
        except (ValueError, RecursionError):
            ev = None
        if isinstance(ev, dict):
            events.append(ev)
        else:
            bad += 1
    stamps = [e["ts"] for e in events if isinstance(e.get("ts"), str)]
    observed.update({"from": stamps[0] if stamps else None, "to": stamps[-1] if stamps else None})
    if bad:
        return None, observed, "%d line(s) of the event log are not JSON objects" % bad
    return events, observed, None


# ───────────────────────────────────── completions ─────────────────────────────────────

def tracker_state(tracker_dir):
    """(the tracker's `state` module, None) or (None, reason)."""
    if not (Path(tracker_dir) / "pravaha_tracker" / "state.py").is_file():
        return None, "the tracker is not at %s" % tracker_dir
    if str(tracker_dir) not in sys.path:
        sys.path.insert(0, str(tracker_dir))
    try:
        from pravaha_tracker import state  # noqa: PLC0415
    except Exception as e:      # noqa: BLE001 — whatever the import raises, the figure is unknown
        return None, "the tracker cannot be imported (%s)" % type(e).__name__
    return state, None


def verdict_figures(events, observed, problem):
    """accepted heads and the rejection rate: the event log alone decides them."""
    if events is None:
        return (unknown(problem, scope("distinct heads carrying a verdict", None), observed),
                unknown(problem, scope("verdict events", None), observed))
    last, verdicts, rejected = {}, 0, 0
    for ev in events:
        if ev.get("kind") != "verdict":
            continue
        verdicts += 1
        rejected += ev.get("result") == "REJECTED"
        if isinstance(ev.get("head"), str) and HEX40.match(ev["head"]):
            last[(ev.get("item"), ev["head"], ev.get("phase", "pre_merge"))] = ev.get("result")
    accepted = sorted({k[1] for k, result in last.items() if result == "ACCEPTED"}
                      - {k[1] for k, result in last.items() if result != "ACCEPTED"})
    heads = fig(accepted, scope("distinct heads carrying a verdict", len({k[1] for k in last})), observed,
                count=len(accepted))
    if verdicts:
        rate = fig(round(rejected / verdicts, 4), scope("verdict events", verdicts), observed, rejected=rejected)
    else:
        rate = unknown("no verdict event is recorded", scope("verdict events", 0), observed)
    return heads, rate


def completions(events, observed, problem, model_path, tracker_dir):
    heads, rate = verdict_figures(events, observed, problem)
    names = {"guarded_completed": "items completed by guarded event", "decision_completions": "decision items",
             "joins": "join items", "weighted_progress": "items in the model"}

    def all_unknown(why):
        out = {k: unknown(why, scope(v, None), observed) for k, v in names.items()}
        out.update(accepted_heads=heads, rejection_rate=rate)
        return out
    if events is None:
        return all_unknown(problem)
    if not model_path:
        return all_unknown("no plan model was given (--model M, or PRAVAHA_PLAN_MODEL)")
    model, err = kyaction.read_json(model_path)
    if err or not isinstance(model, dict) or not isinstance(model.get("items"), list):
        return all_unknown("the plan model %s is %s" % (model_path, err or "not a model"))
    state, err = tracker_state(tracker_dir)
    if err:
        return all_unknown(err)
    try:
        snap = state.build_snapshot(model, events, {}, {}, {})
        rows = {row["id"]: row for track in snap["tracks"] for row in track["items"]}
        kinds = {it["id"]: it.get("done_by") for it in model["items"]}
        pct, total = snap["overall"]["pct"], snap["overall"]["total"]
    except Exception as e:      # noqa: BLE001 — a model or a log the tracker cannot replay measures nothing
        return all_unknown("the tracker could not replay the event log (%s)" % type(e).__name__)
    if set(rows) != set(kinds):
        return all_unknown("the tracker's snapshot does not show every item of the model")

    def done(kind, source=None):
        return sorted(i for i, row in rows.items() if kinds[i] == kind and row.get("status") == "done"
                      and (source is None or row.get("source") == source))

    def count(kind):
        return sum(1 for k in kinds.values() if k == kind)
    basis = "event log only: no detector result is consulted"
    out = {"accepted_heads": heads, "rejection_rate": rate}
    plain = sum(1 for k in kinds.values() if k not in ("decision", "join"))
    if (model.get("control_plane") or {}).get("guarded_completion") is True:
        ids = done(None, "guarded:event")
        out["guarded_completed"] = fig(ids, scope(names["guarded_completed"], plain), observed, count=len(ids))
    else:
        out["guarded_completed"] = unknown("the model does not declare control_plane.guarded_completion: a done "
                                           "event there is not a guarded completion",
                                           scope(names["guarded_completed"], plain), observed)
    for key, kind in (("decision_completions", "decision"), ("joins", "join")):
        ids = done(kind)
        out[key] = fig(ids, scope(names[key], count(kind)), observed, count=len(ids))
    if isinstance(pct, (int, float)) and not isinstance(pct, bool) and is_int(total) and total > 0:
        out["weighted_progress"] = fig(pct, scope(names["weighted_progress"], total), observed, unit="percent",
                                       basis=basis)
    else:
        out["weighted_progress"] = unknown("the model has no items", scope(names["weighted_progress"], total),
                                           observed)
    return out


# ───────────────────────────────────── jobs ─────────────────────────────────────

def read_jobs(run):
    """([(directory name, state | None, problem | None)], None) or (None, reason when there is no job directory)."""
    root = Path(run) / "jobs"
    try:
        names = sorted(p.name for p in root.iterdir() if p.is_dir())
    except FileNotFoundError:
        return None, "no job state is recorded under %s (KV3-B-KYDJOBS)" % root
    except OSError as e:
        return None, "%s cannot be listed (%s)" % (root, type(e).__name__)
    out = []
    for name in names:
        doc, err = kyaction.read_json(root / name / "state.json")
        if err is None and not isinstance(doc, dict):
            doc, err = None, "unreadable: not an object"
        out.append((name, doc, err))
    return out, None


def jobs_section(run, jobs, problem, observed):
    where = "job state records under %s" % (Path(run) / "jobs")
    if jobs is None:
        why = unknown(problem, scope(where, None), observed)
        return {"count": why, "by_phase": dict(why), "by_outcome": dict(why), "failure_fingerprints": dict(why),
                "rows": []}
    den = scope(where, len(jobs))
    rows, phases, outcomes, prints = [], collections.Counter(), collections.Counter(), {}
    unreadable = 0
    for name, doc, err in jobs:
        doc = doc or {}
        row = {"job_dir": name, "state": err or "read"}
        for key in JOB_KEYS + ("outcome", "failure_fp", "attempt"):
            row[key] = doc[key] if doc.get(key) is not None else UNKNOWN
        if isinstance(doc.get("result_event"), dict):
            row["result_event"] = "present"
        rows.append(row)
        unreadable += err is not None
        phases[row["phase"] if isinstance(row["phase"], str) else UNKNOWN] += 1
        outcomes[row["outcome"] if isinstance(row["outcome"], str) else UNKNOWN] += 1
        fp = text(doc.get("failure_fp"))
        if fp:
            entry = prints.setdefault(fp, {"jobs": 0, "max_attempt": None})
            entry["jobs"] += 1
            attempt = doc.get("attempt")
            if not is_int(attempt):
                entry["max_attempt"] = UNKNOWN
            elif entry["max_attempt"] != UNKNOWN:
                entry["max_attempt"] = max(entry["max_attempt"] or 0, attempt)
    if unreadable:
        fps = unknown("%d job state record(s) cannot be read" % unreadable, den, observed)
    else:
        fps = fig(prints, den, observed)
    return {"count": fig(len(jobs), den, observed), "by_phase": fig(dict(phases), den, observed),
            "by_outcome": fig(dict(outcomes), den, observed), "failure_fingerprints": fps, "rows": rows}


# ───────────────────────────────────── tokens ─────────────────────────────────────

def baseline_state(run):
    """(receipt, None) when the baseline is verified as installed, else (None, why)."""
    path = Path(run) / "BASELINE_RECEIPT.json"
    doc, err = kyaction.read_json(path)
    if err:
        return None, "%s is %s: no verified baseline" % (path, err)
    if not isinstance(doc, dict) or not HEX40.match(str(doc.get("source_commit"))) \
            or not HEX64.match(str(doc.get("sha256"))) or not HEX64.match(str(doc.get("review_receipt_sha256"))) \
            or not text(doc.get("path")) or not text(doc.get("installed_path")) \
            or not os.path.isabs(doc["installed_path"]) or "parent_includes_children" not in doc:
        return None, "%s is not a baseline receipt" % path
    found = kyaction.sha_file(doc["installed_path"])
    if found != doc["sha256"]:
        return None, "installed_path %s does not hash to the receipt's sha256 (%s)" \
            % (doc["installed_path"], "unreadable" if found is None else "it is %s" % found[:12])
    return doc, None


def run_baseline(installed_path, run):
    """({session id: four classes}, None) from the one adapter, or (None, why). OUT lives in a private temporary
    directory that is removed again."""
    tmp = private_tmp()
    try:
        out = os.path.join(tmp, "baseline.json")
        rc, _, err = helper([sys.executable, "-B", installed_path, "--json", out], run, BASELINE_TIMEOUT_S)
        if rc != 0:
            return None, "the installed baseline did not run (%s)" % ("exit %s" % rc if rc is not None else err)
        doc, err = kyaction.read_json(out)
        if err or not isinstance(doc, dict) or any(k not in doc for k in BASELINE_KEYS) \
                or not isinstance(doc["top_sessions"], list):
            return None, "the baseline's output lacks one of %s" % ", ".join(BASELINE_KEYS)
        sessions = {}
        for row in doc["top_sessions"]:
            if not isinstance(row, dict) or not text(row.get("key")):
                continue
            use = {name: row.get(key) for key, name in BASELINE_CLASSES.items()}
            if all(is_int(v) and v >= 0 for v in use.values()):
                sessions[row["key"]] = use
        return sessions, None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def baseline_row(sessions, session):
    """the baseline's usage of one session id: its key is the id, or <provider>:<id>."""
    hits = [use for key, use in sessions.items() if key == session or key.endswith(":" + session)]
    return hits[0] if len(hits) == 1 else None


def result_usage(event):
    """the four classes of a stream `result` event, or None."""
    use = event.get("usage") if isinstance(event, dict) and event.get("type") == "result" else None
    if not isinstance(use, dict) or not all(is_int(use.get(k)) and use[k] >= 0 for k in CLASSES):
        return None
    return {k: use[k] for k in CLASSES}


def role_identities(doc):
    """every distinct session identity a role state names."""
    found = set()
    for holder in (doc, doc.get("session") if isinstance(doc.get("session"), dict) else {}):
        for key in ("session_id", "provider_session_id", "id"):
            if holder is doc and key == "id":
                continue
            if text(holder.get(key)):
                found.add(holder[key])
    return sorted(found)


def owners(run, jobs):
    """→ (claims, uncovered, not_started). A claim: {session, owner, role, kind, child, event}."""
    claims, uncovered, not_started = [], [], []
    for name, doc, err in jobs or []:
        owner = "job:" + name
        if doc is None:
            uncovered.append({"owner": owner, "session": None, "why": "job state %s" % err})
            continue
        session, event = text(doc.get("provider_session_id")), doc.get("result_event")
        if session is None:
            if doc.get("phase") == "prepared" and event is None:
                not_started.append(name)             # prepared and never launched: it owns no session
            else:
                uncovered.append({"owner": owner, "session": None,
                                  "why": "no provider_session_id is recorded for this job"})
            continue
        parent = {k: doc[k] for k in ("parent_session_id", "parent_job_id") if doc.get(k) is not None}
        claims.append({"session": session, "owner": owner, "role": text(doc.get("role")) or UNKNOWN,
                       "kind": text(doc.get("kind")) or UNKNOWN, "event": event, "child": bool(parent),
                       "parent": parent, "jobs": {name, text(doc.get("job_id"))} - {None}})
    for role, name in ROLE_STATES:
        doc, err = kyaction.read_json(Path(run) / name)
        if err == "missing":
            continue                                 # no such role state: no interactive session is claimed
        owner = "role_state:" + role
        if err or not isinstance(doc, dict):
            uncovered.append({"owner": owner, "session": None, "why": "%s is %s" % (name, err or "not an object")})
            continue
        ids = role_identities(doc)
        if len(ids) != 1:
            uncovered.append({"owner": owner, "session": None,
                              "why": "%s names %d session identities; exactly one owns the session"
                                     % (name, len(ids))})
            continue
        claims.append({"session": ids[0], "owner": owner, "role": role, "kind": "interactive", "event": None,
                       "child": False, "parent": {}, "jobs": set()})
    return claims, uncovered, not_started


def parent_session(parent, job_sessions):
    """the one session a child's recorded parent names — its parent_session_id, or the session of its
    parent_job_id — → (session, None) or (None, why)."""
    found = set()
    sid, jid = parent.get("parent_session_id"), parent.get("parent_job_id")
    if sid is not None:
        if text(sid) is None:
            return None, "its parent_session_id %s is not a session id" % json.dumps(sid)
        found.add(sid)
    if jid is not None:
        hits = job_sessions.get(jid, set()) if text(jid) else set()
        if len(hits) != 1:
            return None, "its parent_job_id %s names no one recorded job session" % json.dumps(jid)
        found |= hits
    if len(found) != 1:
        return None, "its parent_session_id and parent_job_id name different sessions"
    return found.pop(), None


def add(total, use):
    for k in CLASSES:
        total[k] = total.get(k, 0) + use[k]
    total["total"] = sum(total[k] for k in CLASSES)
    return total


def tokens_section(run, jobs, jobs_problem, observed, guarded):
    receipt, baseline_why = baseline_state(run)
    baseline = signal("verified_installed", str(Path(run) / "BASELINE_RECEIPT.json"),
                      source_commit=receipt["source_commit"], sha256=receipt["sha256"],
                      installed_path=receipt["installed_path"],
                      parent_includes_children=receipt["parent_includes_children"]) if receipt \
        else signal(UNKNOWN, str(Path(run) / "BASELINE_RECEIPT.json"), baseline_why)
    claims, uncovered, not_started = owners(run, jobs)
    by_session = collections.OrderedDict()
    for claim in claims:
        by_session.setdefault(claim["session"], []).append(claim)
    need_baseline = [s for s, group in by_session.items() if all(c["event"] is None for c in group)]
    from_baseline, baseline_run_why = {}, None
    if receipt and need_baseline:
        from_baseline, baseline_run_why = run_baseline(receipt["installed_path"], run)
        from_baseline = from_baseline or {}
    includes = receipt["parent_includes_children"] if receipt else None
    job_sessions = {}
    for claim in claims:
        for job in claim["jobs"]:
            job_sessions.setdefault(job, set()).add(claim["session"])
    sessions, inside = [], []
    for session, group in by_session.items():
        first = group[0]
        entry = {"session": session, "owner": first["owner"], "role": first["role"], "kind": first["kind"],
                 "child": any(c["child"] for c in group), "duplicates_dropped": 0, "source": None, "usage": None}
        payloads = {kyaction.canonical(c["event"]) for c in group if c["event"] is not None}
        why = None
        if entry["child"] and includes is True:
            entry["source"] = "included_in_parent"   # inside its parent's usage: never added again …
            inside.append((entry, group))            # … once that parent is shown to be counted here (below)
        elif entry["child"] and includes is not False:
            why = "a child session, and the baseline receipt's parent_includes_children is not proven (it is %s)" \
                  % json.dumps(includes)
        elif len(payloads) > 1:
            why = "%d different result events name this session: ownership of its usage is not established" \
                  % len(payloads)
        elif payloads:
            entry["usage"] = result_usage(next(c["event"] for c in group if c["event"] is not None))
            entry["source"] = "result_event"
            entry["duplicates_dropped"] = sum(1 for c in group if c["event"] is not None) - 1
            if entry["usage"] is None:
                why = "its result event does not carry the four usage classes as integers"
        elif receipt is None:
            why = "no result event, and no verified baseline to count it from"
        elif baseline_run_why:
            why = "no result event; %s" % baseline_run_why
        else:
            entry["usage"] = baseline_row(from_baseline, session)
            entry["source"] = "baseline"
            if entry["usage"] is None:
                why = "no result event, and the baseline's top_sessions does not cover it"
        if why:
            entry["source"] = None
            uncovered.append({"owner": first["owner"], "session": session, "why": why})
        sessions.append(entry)
    counted_sessions = {s["session"] for s in sessions if s["usage"] is not None}
    for entry, group in inside:
        for claim in (c for c in group if c["child"]):
            parent, why = parent_session(claim["parent"], job_sessions)
            if why is None and parent not in counted_sessions:
                why = "its parent session %s is not counted in this report" % json.dumps(parent)
            if why:
                entry["source"] = None
                uncovered.append({"owner": claim["owner"], "session": entry["session"],
                                  "why": "a child session left out as inside its parent, but %s" % why})
                break

    counted = [s for s in sessions if s["usage"] is not None]
    total, by_role, by_kind = {}, {}, {}
    for s in counted:
        add(total, s["usage"])
        add(by_role.setdefault(s["role"], {}), s["usage"])
        add(by_kind.setdefault(s["kind"], {}), s["usage"])
    den = scope("provider sessions owned by a job or a role state", len(sessions) if jobs is not None else None)
    why = None
    if jobs is None:
        why = jobs_problem
    elif receipt is None:
        why = "no verified baseline: %s" % baseline_why
    elif uncovered:
        why = "%d session(s) or owner(s) are not covered" % len(uncovered)
    elif not sessions:
        why = "no provider session is recorded: nothing was measured"
    elif not counted:
        why = "no session's usage is counted"
    if why:
        def part(value):
            return unknown(why, den, observed, partial=value) if counted else unknown(why, den, observed)
        figures = {"total": part(total), "by_role": part(by_role), "by_kind": part(by_kind)}
    else:
        figures = {"total": fig(total, den, observed), "by_role": fig(by_role, den, observed),
                   "by_kind": fig(by_kind, den, observed)}
    completed = guarded.get("count") if guarded.get("value") != UNKNOWN else None
    per_den = scope("distinct guarded-completed item ids", completed)
    if why or any(k not in total for k in CLASSES):
        figures["per_guarded_completion"] = unknown("the token total is unknown", per_den, observed)
    elif not is_int(completed) or completed < 1:
        figures["per_guarded_completion"] = unknown("no guarded completion is measured to divide by", per_den,
                                                    observed)
    else:
        figures["per_guarded_completion"] = fig(dict({k: round(total[k] / completed, 1) if completed > 1
                                                      else total[k] for k in CLASSES + ("total",)}),
                                                per_den, observed)
    return dict(figures, classes=list(CLASSES), baseline=baseline, sessions=sessions, uncovered=uncovered,
                not_started_jobs=not_started)


# ───────────────────────────────────── signals ─────────────────────────────────────

def loop_state(run, loop):
    """(the loop's state as `kyloop.py admin show` prints it, child state, None) or (None, None, why)."""
    source = FLEET / "kyloop.py"
    if not source.is_file():
        return None, None, "kyloop.py is not installed beside this file"
    rc, out, err = ask("kyloop.py", ("admin", "show", loop), run)
    doc = parse_object(out) if rc == 0 else None
    if doc is None:
        return None, None, "`kyloop.py admin show %s` gave no state (%s)" % (loop, rc if rc is not None else err)
    if doc.get("present") is not True:
        return None, None, "no readable loop state: %s" % doc.get("error")
    rc, out, err = ask("kyloop.py", ("admin", "child", loop), run)
    child = out.split()[0] if rc == 0 and out.split() else None
    return doc, child if child in CHILD_STATES else UNKNOWN, None


def loop_health(run, loop, doc, child, why, now):
    """*loop healthy* (§13). STOPPED: $KY_RUN/STOP_<loop> exists or `enabled` is false. HEALTHY needs all of:
    the controller's pid + process_start alive (R2: process_matches is True); bundle.receipt_sha256 = sha256 of
    $KY_RUN/INSTALL_RECEIPT.json now; and — a child is expected → it is `alive`; none is expected → a recorded
    waiting state, child `none`, last_iteration_at at most 120 s old. A condition that positively fails is
    UNHEALTHY; one that cannot be judged (and none failing) is unknown. A loaded plist is never looked at."""
    source = "kyloop.py admin show %s; admin child %s" % (loop, loop)
    if (Path(run) / ("STOP_" + loop)).exists():
        return signal("STOPPED", source, ["%s exists" % (Path(run) / ("STOP_" + loop))])
    if doc is None:
        return signal(UNKNOWN, source, why)
    if doc.get("enabled") is False:
        return signal("STOPPED", source, ["enabled is false: %s" % kyaction.flat(doc.get("reason"), 120)])
    failed, unjudged = [], []
    controller = doc.get("controller")
    if not isinstance(controller, dict) or not is_int(controller.get("pid")):
        failed.append("no controller identity is recorded")
    else:
        alive = kyaction.process_matches(controller["pid"], controller.get("process_start"))
        if alive is False:
            failed.append("the recorded controller (pid %s) is not running" % controller["pid"])
        elif alive is None:
            unjudged.append("the recorded controller's identity cannot be compared")
    bundle = doc.get("bundle")
    recorded = bundle.get("receipt_sha256") if isinstance(bundle, dict) else None
    current = kyaction.sha_file(Path(run) / "INSTALL_RECEIPT.json")
    if not isinstance(recorded, str) or current is None or recorded != current:
        failed.append("the verified bundle is not the installation receipt as it is now")
    expected, waiting = doc.get("expected_child"), doc.get("waiting")
    age = None
    if expected is not None:
        if child == UNKNOWN:
            unjudged.append("the expected child's state cannot be told")
        elif child != "alive":
            failed.append("the expected child is %s, not alive" % child)
    else:
        if not text(waiting):
            failed.append("no child is expected and no waiting state is recorded")
        if child == UNKNOWN:
            unjudged.append("whether a child is left over cannot be told")
        elif child != "none":
            failed.append("no child is expected but an unreconciled child is recorded (%s)" % child)
        stamp = kyaction.parse_utc(doc.get("last_iteration_at"))
        if stamp is None:
            failed.append("no successful control iteration is recorded")
        else:
            age = round(now - stamp, 1)
            if age > ITERATION_MAX_AGE_S or age < -CLOCK_SLACK_S:
                failed.append("the last successful control iteration is %s s old (limit %d s)"
                              % (age, ITERATION_MAX_AGE_S))
    value = "UNHEALTHY" if failed else UNKNOWN if unjudged else "HEALTHY"
    return signal(value, source, failed + unjudged, child=child, waiting=waiting if text(waiting) else None,
                  expected_child=expected is not None, last_iteration_age_s=age,
                  controller_id=controller.get("controller_id") if isinstance(controller, dict) else None)


def loop_progress(run, loop, doc, why):
    """*loop making progress* = accepted work or a changed external dependency, as the controller judged its last
    run. A zero count alone proves nothing (it is also the default), and no timestamp is read."""
    source = "kyloop.py admin show %s: no_progress_count; %s" % (loop, Path(run) / "loops" / loop)
    if doc is None:
        return signal(UNKNOWN, source, why)
    count = doc.get("no_progress_count")
    if not is_int(count) or count < 0:
        return signal(UNKNOWN, source, "no_progress_count is not recorded as a count")
    if count > 0:
        return signal("NO_PROGRESS", source, "%d consecutive run(s) without accepted work or a changed dependency"
                      % count, no_progress_count=count)
    last = doc.get("last_run_id")
    record = None
    if isinstance(last, str) and re.match(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}\Z", last):
        record, _ = kyaction.read_json(Path(run) / "loops" / loop / (last + ".json"))
    if isinstance(record, dict) and record.get("run_id") == last and record.get("progressed") is True:
        return signal("PROGRESS", source, no_progress_count=0, last_run_id=last,
                      accepted=len(record["accepted"]) if isinstance(record.get("accepted"), list) else UNKNOWN,
                      dependency_changed=record.get("dependency_changed")
                      if isinstance(record.get("dependency_changed"), bool) else UNKNOWN)
    return signal(UNKNOWN, source, "the count is zero and no run judged `progressed` is recorded as the last run",
                  no_progress_count=0)


def probe_pass(run, role):
    """*probe PASS* = `kyqualify.py check <receipt> --config <launch config> --require-context launchd
    --verify-evidence` says PASS and exits 0; REFUSED with exit 1 is the negative; anything else is unknown."""
    source = "kyqualify.py check --require-context launchd --verify-evidence (%s)" % role
    for name in ("kyloop.py", "kyqualify.py"):
        if not (FLEET / name).is_file():
            return signal(UNKNOWN, source, "%s is not installed beside this file" % name)
    rc, out, err = ask("kyloop.py", ("admin", "expected-qualification", role), run)
    expected = parse_object(out) if rc == 0 else None
    receipt = text(expected.get("receipt_path")) if expected else None
    rc2, config = None, ""
    if receipt is not None:
        rc2, config, _ = ask("kyloop.py", ("admin", "launch-config", role), run)
    if receipt is None or rc2 != 0 or parse_object(config) is None:
        return signal(UNKNOWN, source, "kyloop.py could not name this role's launch configuration and receipt")
    tmp = private_tmp()
    try:
        path = os.path.join(tmp, "launch_config.json")
        with open(path, "w", encoding="utf-8") as f:
            f.write(config)
        rc, out, err = helper(py("kyqualify.py", "check", receipt, "--config", path, "--require-context",
                                 "launchd", "--verify-evidence"), run, 600.0)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    said = parse_object(out) or {}
    if rc == 0 and said.get("check") == "PASS" and said.get("reasons") == []:
        return signal("PASS", source, receipt=receipt)
    if rc == 1 and said.get("check") == "REFUSED" and said.get("reasons"):
        return signal("REFUSED", source, [kyaction.flat(r, 200) for r in said["reasons"]][:20], receipt=receipt)
    return signal(UNKNOWN, source, "the check gave no verdict (exit %s)" % (rc if rc is not None else err),
                  receipt=receipt)


def journal_submissions(run):
    """({message of every `- <UTC> [<level>] <message> [notify=submitted]` line}, None) or (None, why). Lines
    split at LF only, as kynotify.sh writes them and kyveto.py reads them."""
    try:
        with open(Path(run) / "JOURNAL_COCKPIT.md", "rb") as f:
            data = f.read()
    except FileNotFoundError:
        return [], None
    except OSError as e:
        return None, "the cockpit journal cannot be read (%s)" % type(e).__name__
    out = []
    for raw in data.split(b"\n"):
        try:
            m = NOTIFY_LINE.match(raw.decode("utf-8").rstrip("\r"))
        except UnicodeDecodeError:
            continue
        if m and m.group(3) == "submitted" and kyaction.parse_utc(m.group(1)) is not None:
            out.append(m.group(2))
    return out, None


def surrogate_signals(run):
    """surrogate_decision, veto_expired and owner_notified from `kyveto.py status` (exit 0, or 3 = attention).
    A decision IS its state; a row the handler flags with an anomaly has a state nothing backs: unknown. The veto
    window `expired` only where the handler itself made the decision effective (its DONE publish record, written
    under the decision lock); it has `not_expired` while time remains or after a veto. *Owner notified* needs the
    record's notification.submitted AND kynotify.sh's journal line; whether the owner READ it is unknown."""
    source = "kyveto.py status"
    names = ("surrogate_decision", "veto_expired", "owner_notified")
    if not (FLEET / "kyveto.py").is_file():
        return {k: signal(UNKNOWN, source, "kyveto.py is not installed beside this file") for k in names}
    rc, out, err = ask("kyveto.py", ("status",), run)
    report = parse_object(out) if rc in (0, 3) else None
    rows = report.get("decisions") if report else None
    if not isinstance(rows, list) or any(not isinstance(r, dict) or not text(r.get("id")) for r in rows):
        why = "`kyveto.py status` gave no decision list (exit %s)" % (rc if rc is not None else err)
        return {k: signal(UNKNOWN, source, why) for k in names}
    journal, journal_why = journal_submissions(run)
    states, expired, notified = {}, {}, {}
    for row in rows:
        did, state = row["id"], row.get("state")
        backed = state in DECISION_STATES and "anomaly" not in row
        states[did] = state if backed else UNKNOWN
        if not backed:
            expired[did] = UNKNOWN
        elif row.get("made_effective_by_handler") is True:
            expired[did] = "expired"
        elif state == "VETOED" or (state == "PENDING_VETO" and is_int(row.get("seconds_remaining"))
                                   and row["seconds_remaining"] > 0):
            expired[did] = "not_expired"
        else:
            expired[did] = UNKNOWN
        if journal is None:
            notified[did] = UNKNOWN
        elif row.get("notification_submitted") is True and any(m.startswith(did + ":") for m in journal):
            notified[did] = "submitted"
        elif isinstance(row.get("notification_submitted"), bool):
            notified[did] = "not_submitted"
        else:
            notified[did] = UNKNOWN
    den = scope("decisions in the surrogate log", len(rows))
    return {"surrogate_decision": signal(states, source, denominator=den,
                                         attention=report.get("attention") is True),
            "veto_expired": signal(expired, source + ": made_effective_by_handler, seconds_remaining",
                                   denominator=den),
            "owner_notified": signal(notified, source + ": notification_submitted; %s"
                                     % (Path(run) / "JOURNAL_COCKPIT.md"), journal_why, denominator=den,
                                     read_by_owner=UNKNOWN)}


def wave_b_done(run):
    """*WAVE_B_DONE* is derived, never a file's existence: the marker must bind the final installation receipt and
    the manifest exactly as they are now (kyloop.py verify_wave_b_done, plus the manifest it also records)."""
    run = Path(run)
    source = str(run / "WAVE_B_DONE")
    if not (run / "WAVE_B_DONE").exists():
        return signal("NOT_DERIVED", source, "no marker has been derived")
    marker, err = kyaction.read_json(run / "WAVE_B_DONE")
    receipt, rerr = kyaction.read_json(run / "INSTALL_RECEIPT.json")
    problems = []
    if err or not isinstance(marker, dict):
        problems.append("the marker is not a record (its existence is not evidence)")
        marker = {}
    if rerr or not isinstance(receipt, dict) or receipt.get("mode") != "final":
        problems.append("the installation receipt is not a final receipt")
    for key, name in (("final_receipt_sha256", "INSTALL_RECEIPT.json"), ("versions_sha256", "VERSIONS.json")):
        now = kyaction.sha_file(run / name)
        if now is None or marker.get(key) != now:
            problems.append("the marker's %s is not the sha256 of %s now" % (key, name))
    return signal("UNVERIFIED", source, problems) if problems else \
        signal("DONE", source, final_receipt_sha256=marker["final_receipt_sha256"])


def ready_to_start(run, unavailable):
    """*READY_TO_START* = the release / final-acceptance detector re-run now: `kygate.sh --pre-resume` prints
    READY_TO_START and exits 0, or WAIT and exits 75. Any other pairing is unknown."""
    source = "kygate.sh --pre-resume"
    gate = FLEET / "kygate.sh"
    if not gate.is_file():
        unavailable.append("kygate.sh")
        return signal(UNKNOWN, source, "kygate.sh is not installed beside this file (KV3-B-KYGATE)")
    rc, out, err = helper(["/bin/bash", gate, "--pre-resume"], run, GATE_TIMEOUT_S)
    lines = out.split("\n")
    reasons = [line[len("reason="):] for line in lines if line.startswith("reason=")][:40]
    if rc == 0 and lines[0] == "READY_TO_START":
        return signal("READY_TO_START", source)
    if rc == 75 and lines[0] == "WAIT":
        return signal("WAIT", source, "the gate is not open", reasons=reasons)
    return signal(UNKNOWN, source, "the gate gave no verdict (exit %s, first line %r)"
                  % (rc if rc is not None else err, kyaction.flat(lines[0], 60)))


def signals_section(run, now, unavailable):
    health, progress = {}, {}
    for loop in LOOPS:
        doc, child, why = loop_state(run, loop)
        health[loop] = loop_health(run, loop, doc, child, why, now)
        progress[loop] = loop_progress(run, loop, doc, why)
    unavailable.extend(name for name in ("kyloop.py", "kyveto.py", "kyqualify.py") if not (FLEET / name).is_file())
    out = {"loop_healthy": health, "loop_progress": progress,
           "probe_pass": {role: probe_pass(run, role) for role in PROBE_ROLES},
           "platform_approval": signal(UNKNOWN, "kyreport.py approval --expect X",
                                       "an approval is verified only by a readback bound to its repository, run, "
                                       "attempt, environment, source SHA and approver: run `kyreport.py approval "
                                       "--expect X`; an owner's report alone is approval_reported_unverified"),
           "WAVE_B_DONE": wave_b_done(run), "READY_TO_START": ready_to_start(run, unavailable)}
    out.update(surrogate_signals(run))
    return out


# ───────────────────────────────────── the report ─────────────────────────────────────

def report(run, events_path, model_path, tracker_dir):
    now = time.time()
    events, observed, problem = read_events(events_path)
    jobs, jobs_problem = read_jobs(run)
    unavailable = []
    done = completions(events, observed, problem, model_path, tracker_dir)
    no_source = "KV3-B-KYREPORT names no source for this figure"
    return {"schema": SCHEMA, "mode": "status", "generated_at": kyaction.utc(now), "run_dir": str(run),
            "observed": observed, "completions": done,
            "jobs": jobs_section(run, jobs, jobs_problem, observed),
            "tokens": tokens_section(run, jobs, jobs_problem, observed, done["guarded_completed"]),
            "signals": signals_section(run, now, unavailable),
            "not_measured": {k: unknown(no_source, scope(k, None), observed)
                             for k in ("no_progress_jobs", "escalations", "ci_infra_retries", "lead_time_p50_p90")},
            "savings": CANNOT, "throughput": CANNOT, "helpers_unavailable": sorted(set(unavailable))}


# ───────────────────────────────────── platform approval ─────────────────────────────────────

def load_expectation(arg):
    """the expectation X (a JSON file, or the JSON object itself) → (doc, None) or (None, problem)."""
    if arg.lstrip().startswith("{"):
        doc = parse_object(arg)
        err = None if doc is not None else "not a JSON object"
    else:
        doc, err = kyaction.read_json(arg)
    if err or not isinstance(doc, dict):
        return None, "--expect %s" % (err or "is not an object")
    checks = (("repository", lambda v: isinstance(v, str) and REPO_RE.match(v)),
              ("run_id", lambda v: is_int(v) and v > 0), ("run_attempt", lambda v: is_int(v) and v > 0),
              ("environment", text), ("source_sha", lambda v: isinstance(v, str) and HEX40.match(v)),
              ("required_approver", text))
    bad = [name for name, ok in checks if not ok(doc.get(name))]
    return (None, "--expect lacks a usable %s" % ", ".join(bad)) if bad else (doc, None)


def gh_api(gh, path, want):
    """(document of type `want`, None) or (None, why) from `gh api <path>` — a GET, nothing else."""
    try:
        r = subprocess.run([gh, "api", path], capture_output=True, text=True, timeout=HELPER_TIMEOUT_S,
                           stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError) as e:
        return None, "`gh api %s` could not be run (%s)" % (path, type(e).__name__)
    if r.returncode != 0:
        return None, "`gh api %s` exited %d" % (path, r.returncode)
    try:
        doc = json.loads(r.stdout)
    except (ValueError, RecursionError):
        doc = None
    return (doc, None) if isinstance(doc, want) else (None, "`gh api %s` did not answer JSON" % path)


def approval(expect, gh):
    """*platform approval verified* (§13): the run attempt read back from GitHub is the expected repository, run,
    attempt and source SHA, it is the run's latest attempt, and the run's approvals show `approved` by the required
    approver for the expected environment with no rejection of that environment. GitHub lists approvals per run,
    not per attempt, so an expectation for attempt > 1 cannot be bound by this readback and is never `verified`.
    Workflow completion and semantic operation acceptance are separate states and never follow from approval."""
    base = "repos/%s/actions/runs/%d" % (expect["repository"], expect["run_id"])
    attempt, a_err = gh_api(gh, "%s/attempts/%d" % (base, expect["run_attempt"]), dict)
    latest, r_err = gh_api(gh, base, dict)
    approvals, p_err = gh_api(gh, base + "/approvals", list)
    unread = [e for e in (a_err, r_err, p_err) if e]
    mismatch = []
    identified = False
    if attempt is not None and latest is not None:
        repo = attempt.get("repository") if isinstance(attempt.get("repository"), dict) else {}
        for name, got, want in (("repository", repo.get("full_name"), expect["repository"]),
                                ("run_id", attempt.get("id"), expect["run_id"]),
                                ("run_attempt", attempt.get("run_attempt"), expect["run_attempt"]),
                                ("source_sha", attempt.get("head_sha"), expect["source_sha"]),
                                ("latest run_attempt", latest.get("run_attempt"), expect["run_attempt"]),
                                ("latest run_id", latest.get("id"), expect["run_id"])):
            if type(got) is not type(want) or got != want:
                mismatch.append("%s read back as %s, expected %s" % (name, json.dumps(got), json.dumps(want)))
        identified = not mismatch
        if expect["run_attempt"] != 1:
            mismatch.append("approvals are listed per run: one for attempt %d cannot be bound by this readback"
                            % expect["run_attempt"])
    if approvals is not None:
        def for_env(a):
            envs = a.get("environments") if isinstance(a, dict) and isinstance(a.get("environments"), list) else []
            return any(isinstance(e, dict) and e.get("name") == expect["environment"] for e in envs)
        mine = [a for a in approvals if for_env(a)]
        if any(a.get("state") != "approved" for a in mine):
            mismatch.append("the environment %s carries a review that is not `approved`" % expect["environment"])
        elif not any(isinstance(a.get("user"), dict) and a["user"].get("login") == expect["required_approver"]
                     for a in mine):
            mismatch.append("no approval of %s by %s is on record" % (expect["environment"],
                                                                      expect["required_approver"]))
    reported = expect.get("owner_report") not in (None, "", False)
    if not unread and not mismatch:
        value = "verified"
    elif reported:
        value = "approval_reported_unverified"
    else:
        value = "not_verified" if mismatch else UNKNOWN
    source = "%s api %s[/attempts/%d|/approvals]" % (gh, base, expect["run_attempt"])
    if identified:
        status, conclusion = attempt.get("status"), attempt.get("conclusion")
        if status == "completed" and text(conclusion):
            completion = signal(conclusion, source)
        elif text(status) and status != "completed":
            completion = signal(status, source)
        else:
            completion = signal(UNKNOWN, source, "the readback carries no status")
    else:
        completion = signal(UNKNOWN, source, "the run attempt was not read back as the expected one")
    return {"schema": "ky.approval_readback/1", "value": value, "source": source, "why": mismatch + unread,
            "expected": {k: expect[k] for k in ("repository", "run_id", "run_attempt", "environment", "source_sha",
                                                "required_approver")},
            "owner_report": "present" if reported else "absent",
            "external_dependency": "satisfied" if value == "verified" else "kept",
            "workflow_completion": completion,
            "operation_acceptance": signal(UNKNOWN, "the operation's own acceptance evidence",
                                           "semantic acceptance of the operation is not read here: neither an "
                                           "approval nor a completed workflow is evidence of it"),
            "read_at": kyaction.utc()}


# ───────────────────────────────────── baseline import ─────────────────────────────────────

class Refused(Exception):
    pass


def git_blob(repo, commit, path):
    """the bytes of blob <commit>:<path> from the object store of `repo` — never a work-tree file."""
    if not HEX40.match(commit):
        raise Refused("commit_not_exact: --commit must be a full 40-hex commit id, not a name that can move")
    if os.path.isabs(path) or path.startswith("-") or ".." in path.split("/") or ":" in path or not path:
        raise Refused("path_not_in_tree: --path must be a path inside the commit's tree, not a file on disk")
    git = ["git", "-C", str(repo), "--no-replace-objects"]
    try:
        kind = subprocess.run(git + ["cat-file", "-t", commit], capture_output=True, text=True, timeout=60,
                              stdin=subprocess.DEVNULL)
        if kind.returncode != 0 or kind.stdout.strip() != "commit":
            raise Refused("commit_unknown: %s is not a commit in the object store of %s" % (commit, repo))
        entry = "%s:%s" % (commit, path)
        kind = subprocess.run(git + ["cat-file", "-t", entry], capture_output=True, text=True, timeout=60,
                              stdin=subprocess.DEVNULL)
        if kind.returncode != 0 or kind.stdout.strip() != "blob":
            raise Refused("blob_missing: %s is not a file of that commit (a work-tree file is not a source)"
                          % entry)
        blob = subprocess.run(git + ["cat-file", "blob", entry], capture_output=True, timeout=60,
                              stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError) as e:
        raise Refused("git_unavailable: %s" % type(e).__name__) from None
    if blob.returncode != 0:
        raise Refused("blob_unreadable: %s" % entry)
    return blob.stdout


def check_review(receipt_path, commit, path, digest):
    """the review receipt V accepts exactly this blob → sha256 of V, or Refused."""
    doc, err = kyaction.read_json(receipt_path)
    if err or not isinstance(doc, dict):
        raise Refused("review_receipt_unreadable: %s is %s" % (receipt_path, err or "not an object"))
    if doc.get("verdict") != "ACCEPTED":
        raise Refused("review_not_accepted: verdict is %s" % json.dumps(doc.get("verdict")))
    reviewer, author = text(doc.get("reviewer_session_id")), text(doc.get("author_session_id"))
    if reviewer is None or author is None or reviewer == author:
        raise Refused("review_not_independent: reviewer_session_id and author_session_id must both be recorded "
                      "and differ")
    if doc.get("source_commit") != commit:
        raise Refused("review_of_another_commit: the receipt's source_commit is %s"
                      % json.dumps(doc.get("source_commit")))
    inputs = doc.get("inputs")
    if not isinstance(inputs, dict) or inputs.get(path) != digest:
        raise Refused("review_of_other_bytes: the receipt's inputs[%s] is not the blob's sha256 %s" % (path, digest))
    digest_v = kyaction.sha_file(receipt_path)
    if digest_v is None:
        raise Refused("review_receipt_unreadable: %s" % receipt_path)
    return digest_v


def baseline_import(run, repo, commit, path, review_receipt, dest):
    """→ the baseline receipt. Every check comes before the action record: a refusal writes nothing."""
    if not os.path.isabs(dest):
        raise Refused("dest_not_absolute: --dest must be an absolute path")
    blob = git_blob(repo, commit, path)
    digest = kyaction.sha_bytes(blob)
    review_digest = check_review(review_receipt, commit, path, digest)
    if os.path.lexists(dest) and kyaction.sha_file(dest) != digest:
        raise Refused("dest_exists: %s exists and is not this blob; it is not overwritten" % dest)
    receipt_path = Path(run) / "BASELINE_RECEIPT.json"
    receipt = {"schema": "ky.baseline_receipt/1", "source_commit": commit, "path": path, "sha256": digest,
               "review_receipt_sha256": review_digest, "installed_path": str(dest),
               "parent_includes_children": None}
    result = {"sha256": digest, "installed_path": str(dest), "receipt": str(receipt_path)}

    def installed():
        current, _ = kyaction.read_json(receipt_path)
        return kyaction.sha_file(dest) == digest and isinstance(current, dict) \
            and all(current.get(k) == v for k, v in receipt.items() if k != "parent_includes_children")
    action_id = "BASELINE-IMPORT-%s-%s" % (commit[:12], digest[:12])
    actor = {"role": "baseline-import", "holder_kind": "supervisor", "controller_id": "kyreport.baseline-import"}
    try:
        status, record = kyaction.begin(run, action_id, "baseline_import", actor,
                                        {"source_commit": commit, "path": path, "sha256": digest,
                                         "review_receipt_sha256": review_digest},
                                        {"installed_path": str(dest), "receipt": str(receipt_path)},
                                        "baseline: absent → installed")
        if status == "done":
            if not installed():
                raise Refused("installed_baseline_changed: action %s is DONE but %s or %s is no longer what it "
                              "recorded" % (action_id, dest, receipt_path))
            return json.loads(receipt_path.read_text(encoding="utf-8"))
        if status in ("in_progress", "failed"):
            raise Refused("action_%s: %s (state %s)" % (status, action_id, record["state"]))
        if status == "unfinished":
            outcome, _ = kyaction.reconcile(run, action_id,
                                            lambda _r: ("done", result) if installed() else ("not_done", {}),
                                            by=actor["controller_id"])
            if outcome == "done":
                return json.loads(receipt_path.read_text(encoding="utf-8"))
        try:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            if not os.path.lexists(dest):
                with open(dest, "xb") as f:      # exclusive: never through a link somebody placed meanwhile
                    f.write(blob)
                    f.flush()
                    os.fsync(f.fileno())
                os.chmod(dest, 0o444)
            if kyaction.sha_file(dest) != digest:
                raise OSError("the installed file does not hash to the blob")
            kyaction.write_atomic(receipt_path, json.dumps(receipt, indent=1) + "\n")
        except OSError as e:
            kyaction.fail(run, action_id, {"error": "%s: %s" % (type(e).__name__, kyaction.flat(e, 200))})
            raise Refused("install_failed: %s (recorded in action %s)" % (type(e).__name__, action_id)) from None
        kyaction.complete(run, action_id, result)
        return receipt
    except kyaction.ActionError as e:
        raise Refused("action_record: %s" % kyaction.flat(e, 200)) from None


# ───────────────────────────────────── CLI ─────────────────────────────────────

def options(argv, allowed, flags=()):
    """{option: value} for `--opt value` pairs and bare flags, or None on anything else."""
    out = {}
    while argv:
        if argv[0] in flags and argv[0] not in out:
            out[argv[0]] = True
            argv = argv[1:]
        elif argv[0] in allowed and len(argv) >= 2 and argv[0] not in out and argv[1] != "":
            out[argv[0]] = argv[1]
            argv = argv[2:]
        else:
            return None
    return out


def usage():
    print(USAGE, file=sys.stderr)
    return 64


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    run = run_dir(os.environ)
    if argv and argv[0] == "approval":
        opts = options(argv[1:], ("--expect",))
        if not opts or "--expect" not in opts:
            return usage()
        expect, err = load_expectation(opts["--expect"])
        if err:
            print("kyreport: %s" % err, file=sys.stderr)
            return usage()
        out = approval(expect, os.environ.get("KY_GH") or "gh")
        print(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True))
        return 0 if out["value"] == "verified" else 1
    if argv and argv[0] == "baseline-import":
        names = ("--repo", "--commit", "--path", "--review-receipt", "--dest")
        opts = options(argv[1:], names)
        if not opts or any(n not in opts for n in names):
            return usage()
        if not run.is_dir():
            print("kyreport: run directory missing: %s" % run, file=sys.stderr)
            return 66
        try:
            receipt = baseline_import(run, opts["--repo"], opts["--commit"], opts["--path"],
                                      opts["--review-receipt"], opts["--dest"])
        except Refused as e:
            print("kyreport: REFUSED %s" % e, file=sys.stderr)
            return 1
        print(json.dumps(receipt, ensure_ascii=False, indent=1, sort_keys=True))
        return 0
    opts = options(argv, ("--events", "--model"), ("--today",))
    if opts is None:
        return usage()
    if not run.is_dir():
        print("kyreport: run directory missing: %s" % run, file=sys.stderr)
        return 66
    tracker = os.environ.get("KY_TRACKER_LIVE") or str(Path(os.environ.get("KY_ROOT") or "/Users/Dev/kalayantra")
                                                        / "tracker_live")
    out = report(run, opts.get("--events") or str(run / "EVENTS.jsonl"),
                 opts.get("--model") or os.environ.get("PRAVAHA_PLAN_MODEL"), tracker)
    print(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
