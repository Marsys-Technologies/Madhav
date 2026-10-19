"""A7 D-46 sweep: list (dry-run, the default) or write (--apply) every completion D-46 now allows.

D-46 (owner direction 2026-10-17): a code/artifact item is IMPLEMENTED when merged + independently accepted
(criterion v2) + contained in a successful main deploy; an open dependency only makes it `activation_pending`.

Inputs are read-only: the plan model, the event log, the repository's git history (`git merge-base`, `git log`)
and an EVIDENCE FILE supplied by the cockpit (it has `gh`; this module never calls GitHub). Shape, schema
`ky.d46_evidence/1` (every sha is lowercase hex):

    {"schema": "ky.d46_evidence/1", "observed_at": "<iso>", "main_sha": "<40>",
     "prs": [{"number": 3561, "state": "MERGED", "headRefOid": "<40>", "mergeCommit": {"oid": "<40>"},
              "item": "K3-2"}],                        # "item" optional: else the acceptance's pr / detector pr
     "acceptances": [{"item": "K3-2", "criterion": "v2", "result": "ACCEPTED", "actor": "stream-V:<slot>",
                      "ts": "<iso>", "ref": "<review job id or PR comment url>",
                      "pr": 3561, "head": "<40>"}      # code: the exact reviewed head
                     | {... "artifact_digest": "<64>"}],  # artifact (post-deploy acceptances are retired, A8 §4)
     "deploys": [{"run_id": 123, "head_sha": "<40>", "conclusion": "success", "event": "workflow_run",
                  "branch": "main", "created_at": "<iso>"}],
     "detectors": {"K3-2": {"status": "done", "detail": "..."}}}   # optional; --apply asks the live tracker

An item closes only when every piece is present and git agrees: the merge commit is an ancestor of `main_sha`, the
acceptance names the PR's exact head and comes from the model's verdict stream, and a successful workflow_run
deploy of main has a head that CONTAINS the merge commit (read from git, never from the file's say-so).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    __package__ = "pravaha_tracker"

from pravaha_tracker.completion import D46_KINDS, d46_kind, evidence_requirements  # noqa: E402
from pravaha_tracker.events import actor_stream  # noqa: E402
from pravaha_tracker import merged_deployed  # noqa: E402
from pravaha_tracker.state import build_snapshot  # noqa: E402
from pravaha_tracker.verdicts import accepted_verdict  # noqa: E402

SCHEMA = "ky.d46_evidence/1"
SWEEPER = "d46-sweep"


class SweepError(ValueError):
    """The evidence file or an input is unusable; nothing is swept."""


def _sha(value, length: int) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{%d}" % length, value) is not None


def load_evidence(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as handle:
            doc = json.load(handle)
    except (OSError, ValueError) as exc:
        raise SweepError(f"evidence file unreadable: {exc}") from exc
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA:
        raise SweepError(f"evidence file needs schema {SCHEMA!r}")
    for key in ("prs", "acceptances", "deploys"):
        if not isinstance(doc.get(key, []), list):
            raise SweepError(f"evidence {key!r} must be a list")
    if not isinstance(doc.get("detectors", {}), dict):
        raise SweepError("evidence 'detectors' must be an object")
    return doc


def git(repo: str, *args: str) -> tuple[int, str]:
    """Read-only git; never writes, never takes optional locks."""
    proc = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, timeout=60, check=False,
                          env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"})
    return proc.returncode, proc.stdout


def is_ancestor(repo: str, older: str, newer: str) -> bool:
    return _sha(older, 40) and _sha(newer, 40) and git(repo, "merge-base", "--is-ancestor", older, newer)[0] == 0


def squash_commit_for_pr(repo: str, main_sha: str, number: int) -> str | None:
    """Fallback when the evidence omits a merge commit: the squash subject on main ends in `(#N)`."""
    rc, out = git(repo, "log", "--format=%H%x09%s", "--grep", rf"(#{number})$", main_sha)
    for line in out.splitlines() if rc == 0 else []:
        sha, _, subject = line.partition("\t")
        if _sha(sha, 40) and subject.endswith(f"(#{number})"):
            return sha
    return None


def _completed(events: list[dict]) -> set[str]:
    return {e["item"] for e in events if e.get("kind") == "item" and e.get("state") == "done"
            and e.get("guarded") is True and not e.get("step")}


def _item_pr(item: dict, evidence: dict) -> int | None:
    for pr in evidence.get("prs", []):
        if pr.get("item") == item["id"] and isinstance(pr.get("number"), int):
            return pr["number"]
    for acc in evidence.get("acceptances", []):
        if acc.get("item") == item["id"] and isinstance(acc.get("pr"), int):
            return acc["pr"]
    declared = (item.get("detector") or {}).get("pr")
    return declared if isinstance(declared, int) else None


def _acceptance(model, events, evidence, item, *, head=None, digest=None, phase="pre_merge"):
    """→ (ref dict | None). Evidence-file acceptance (criterion v2, independent actor) or the log's own verdict."""
    verdict_stream = model.get("control_plane", {}).get("verdict_stream")
    for acc in reversed(evidence.get("acceptances", [])):
        if (acc.get("item") == item["id"] and acc.get("result") == "ACCEPTED" and acc.get("criterion") == "v2"
                and acc.get("phase", "pre_merge" if head else "artifact") == phase
                and (acc.get("head") == head if head else acc.get("artifact_digest") == digest)
                and actor_stream(acc.get("actor", "")) == verdict_stream):
            return {"source": "evidence", "phase": phase, "head": head, "artifact_digest": digest,
                    "actor": acc["actor"], "ts": acc.get("ts"), "ref": acc.get("ref")}
    logged = accepted_verdict(events, item["id"], head=head, artifact_digest=digest, phase=phase)
    if logged and actor_stream(logged.get("actor", "")) == verdict_stream:
        return {"source": "event_log", "phase": phase, "head": head, "artifact_digest": digest,
                "actor": logged.get("actor"), "ts": logged.get("ts"), "ref": None}
    return None


def _first_deploy(repo, evidence, merge):
    runs = [r for r in evidence.get("deploys", []) if r.get("conclusion") == "success"
            and r.get("event") == "workflow_run" and r.get("branch", "main") == "main" and _sha(r.get("head_sha"), 40)
            and r.get("run_id")]
    for run in sorted(runs, key=lambda r: (str(r.get("created_at")), str(r["run_id"]))):
        if is_ancestor(repo, merge, run["head_sha"]):
            return run
    return None


def classify(model: dict, events: list[dict], evidence: dict, repo: str, derived_done: dict | None = None) -> list[dict]:
    """One report per executable item, in plan order: would_close | already_done | not_applicable | not_closable |
    out_of_scope (operation / packet kinds keep their own completion and are only counted)."""
    snapshot = build_snapshot(model, events, {}, {}, {}, derived_done=derived_done)
    rows = {r["id"]: r for track in snapshot["tracks"] for r in track["items"]}
    done = _completed(events)
    main_sha = evidence.get("main_sha")
    reports = []
    for item in model.get("items", []):
        if item.get("done_by") in ("decision", "join") or item.get("join"):
            continue
        iid, kind = item["id"], item.get("completion_kind")
        report = {"item": iid, "completion_kind": kind, "status": None, "evidence": {}, "missing": [],
                  "activation_pending": []}
        reports.append(report)
        if iid in done:
            report["status"] = "already_done"
            continue
        if rows.get(iid, {}).get("status") == "not_applicable":
            report["status"] = "not_applicable"
            continue
        if kind not in D46_KINDS:
            report["status"] = "out_of_scope"
            continue
        missing, ev = report["missing"], report["evidence"]
        unknown = [d for d in rows[iid]["deps_open"] if d not in rows]
        if unknown:
            missing.append("dependencies unknown to the plan: " + ", ".join(unknown))
        report["activation_pending"] = [d for d in rows[iid]["deps_open"] if d in rows]
        if kind == "code":
            _code_evidence(model, events, evidence, repo, item, main_sha, ev, missing)
        else:
            _artifact_evidence(model, events, evidence, item, ev, missing)
            if set(item.get("steps", [])) - {e.get("step") for e in events if e.get("kind") == "item"
                                             and e.get("item") == iid and e.get("state") == "done" and e.get("step")}:
                missing.append("artifact steps remain open")
        det = evidence.get("detectors", {}).get(iid)
        if det is None:
            ev["detector"] = "not supplied: measured live by --apply"
        elif det.get("status") != "done":
            missing.append("detector has not passed")
        report["status"] = "not_closable" if missing else "would_close"
    return reports


def _code_evidence(model, events, evidence, repo, item, main_sha, ev, missing) -> None:
    number = _item_pr(item, evidence)
    pr = next((p for p in evidence.get("prs", []) if p.get("number") == number), None) if number else None
    if pr is None or pr.get("state") != "MERGED" or not _sha(pr.get("headRefOid"), 40):
        missing.append("merged PR not evidenced")
        return
    merge = (pr.get("mergeCommit") or {}).get("oid") if isinstance(pr.get("mergeCommit"), dict) else None
    if merge is None and _sha(main_sha, 40):
        merge = squash_commit_for_pr(repo, main_sha, number)
    ev.update(merged_pr=number, head=pr["headRefOid"], merge_commit=merge)
    if not _sha(merge, 40) or not _sha(main_sha, 40) or not is_ancestor(repo, merge, main_sha):
        missing.append("merge commit not on main")
        return
    acc = _acceptance(model, events, evidence, item, head=pr["headRefOid"])
    ev["acceptance_ref"] = acc
    if acc is None:
        missing.append("no independent criterion-v2 acceptance at the PR's exact head")
    deploy = _first_deploy(repo, evidence, merge)
    ev["deploy_run_id"] = deploy["run_id"] if deploy else None
    if deploy is None:
        missing.append("no successful main deploy contains the merge commit")
    requirements = evidence_requirements(model, item)
    if requirements and requirements["conflict"]:
        missing.append("declaration conflict: " + requirements["conflict"])


def _artifact_evidence(model, events, evidence, item, ev, missing) -> None:
    import hashlib
    path = (item.get("detector") or {}).get("path")
    if not isinstance(path, str) or not os.path.isfile(path):
        missing.append("declared artifact file absent")
        return
    sha = hashlib.sha256()
    try:
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                sha.update(chunk)
    except OSError:
        missing.append("declared artifact file unreadable")
        return
    digest = sha.hexdigest()
    ev.update(artifact_path=path, artifact_digest=digest)
    acc = _acceptance(model, events, evidence, item, digest=digest, phase="artifact")
    ev["acceptance_ref"] = acc
    if acc is None:
        missing.append("no independent criterion-v2 acceptance at the artifact digest")


def render(reports: list[dict]) -> str:
    counts: dict[str, int] = {}
    for r in reports:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    lines = ["D-46 sweep", "summary: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))]
    for r in reports:
        if r["status"] == "would_close":
            e = r["evidence"]
            lines.append(f"CLOSE  {r['item']} [{r['completion_kind']}] pr={e.get('merged_pr')} "
                         f"deploy_run={e.get('deploy_run_id')} activation_pending={r['activation_pending'] or '-'}")
        elif r["status"] == "not_closable":
            lines.append(f"HOLD   {r['item']} [{r['completion_kind']}] missing: " + "; ".join(r["missing"]))
    return "\n".join(lines)


def apply(model: dict, evidence: dict, repo: str, events_path: str, observe_detector,
          derived_done: dict | None = None) -> list[dict]:
    """Close every would_close item under the event-log lock, through the same guard `done` uses.

    All-or-nothing per item: the verdict / review events an item needs are staged in memory beside its done event,
    the guard judges the would-be log, and only a passing item has anything appended (a refusal leaves no writes).
    """
    from pravaha_tracker.claims import _append, _close, _locked, _read
    from pravaha_tracker.completion import CompletionError, guarded_done_event
    from pravaha_tracker.events import validate, validate_against_model
    results = []
    fd = _locked(events_path)
    try:
        for report in classify(model, _read(fd), evidence, repo, derived_done):
            if report["status"] != "would_close":
                continue
            item = next(i for i in model["items"] if i["id"] == report["item"])
            ev = report["evidence"]
            view, staged = _read(fd), []

            def stage(event: dict) -> None:
                validate_against_model(event, model, view)
                event = validate(event)
                staged.append(event)
                view.append(event)

            owner = str(item.get("owner", "")).upper()
            actor = f"stream-{'S' if owner in ('N', 'V') else owner}:{SWEEPER}"
            try:
                detector = evidence.get("detectors", {}).get(item["id"]) or observe_detector(item["id"])
                if detector.get("status") != "done":    # say what was read, not only that it was not `done`
                    raise CompletionError(f"declared detector has not passed: status {detector.get('status')!r}"
                                          f" ({detector.get('detail')})")
                if report["completion_kind"] == "code":
                    proof = _code_proof(model, view, evidence, repo, item, ev, actor, stage)
                else:
                    _log_verdict(item, ev, stage)
                    proof = {"type": "artifact", "artifact_digest": ev["artifact_digest"], "path": ev["artifact_path"]}
                stage(guarded_done_event(model, view, item["id"], actor, detector, proof, derived_done=derived_done))
            except (CompletionError, ValueError) as exc:
                results.append({"item": item["id"], "closed": False, "refused": str(exc)})
                continue
            written = [_append(fd, event) for event in staged]
            results.append({"item": item["id"], "closed": True, "event": written[-1]})
    finally:
        _close(fd)
    return results


def _log_verdict(item, ev, stage, *, phase="pre_merge") -> None:
    """Stage the cockpit-supplied acceptance as a verdict event, if the log does not hold it yet."""
    acc = ev["acceptance_ref"]
    if acc["source"] == "event_log":
        return
    stage({"kind": "verdict", "actor": acc["actor"], "item": item["id"], "result": "ACCEPTED", "phase": phase,
           "detail": f"D-46 criterion v2 acceptance, ref {acc.get('ref')}; recorded by the {SWEEPER}",
           **({"head": acc["head"]} if acc.get("head") else {"artifact_digest": acc["artifact_digest"]}),
           **({"ts": acc["ts"]} if acc.get("ts") else {})})


def _code_proof(model, events, evidence, repo, item, ev, actor, stage) -> dict:
    _log_verdict(item, ev, stage)
    registered = any(e.get("kind") == "item" and e.get("item") == item["id"] and e.get("state") == "review"
                     and f"PR #{ev['merged_pr']}" in e.get("detail", "") and ev["head"] in e.get("detail", "")
                     for e in events)
    if not registered:
        stage({"kind": "item", "actor": actor, "item": item["id"], "state": "review",
               "detail": f"PR #{ev['merged_pr']} head {ev['head']} registered by the {SWEEPER} (D-46)"})
    run = _first_deploy(repo, evidence, ev["merge_commit"])
    return {"type": "code", "reviewed_head": ev["head"], "repo": repo,
            "pr": {"number": ev["merged_pr"], "state": "MERGED", "headRefOid": ev["head"],
                   "mergeCommit": {"oid": ev["merge_commit"]}},
            "deploy": {"deployed_sha": run["head_sha"], "run_id": run["run_id"], "contains_merge": True,
                       "deployed_at": run.get("created_at")}}


def main(argv=None) -> int:
    from pravaha_tracker import cli
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--evidence", required=True, help="cockpit evidence file (schema ky.d46_evidence/1)")
    ap.add_argument("--model", default=cli.MODEL)
    ap.add_argument("--events", default=cli.EVENTS)
    ap.add_argument("--repo", default=os.environ.get("PRAVAHA_REPO", cli.REPO_ROOT))
    ap.add_argument("--url", default=None,
                    help="live tracker to measure detectors against (default: PRAVAHA_URL, else the Pravāha "
                         f"tracker at {cli.URL}; the KĀLA-YANTRA tracker is http://127.0.0.1:8767)")
    ap.add_argument("--json", action="store_true", help="machine-readable report")
    ap.add_argument("--apply", action="store_true", help="write the completions (default: dry-run, writes nothing)")
    a = ap.parse_args(argv)
    if a.url:
        cli.URL = a.url.rstrip("/")
    try:
        with open(a.model, encoding="utf-8") as handle:
            model = json.load(handle)
        evidence = load_evidence(a.evidence)
        if model.get("control_plane", {}).get("guarded_completion") is not True:
            raise SweepError("model does not enable guarded completion")
        events = []
        try:
            with open(a.events, encoding="utf-8") as handle:
                for raw in handle:
                    try:
                        events.append(json.loads(raw))
                    except ValueError:
                        continue
        except OSError as exc:
            raise SweepError(f"event log unreadable: {exc}") from exc
        # the display's own derivation, so a dependency shown as done by merge+deploy counts here too (SR-BOLD-07)
        source = merged_deployed.GitHubSource(a.repo)
        source.refresh()
        derived = merged_deployed.derive_for_events(model, events, source)
        reports = classify(model, events, evidence, a.repo, derived)
    except (OSError, ValueError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    if not a.apply:
        print(json.dumps(reports, indent=1) if a.json else render(reports))
        return 0

    def observe(item_id: str) -> dict:
        observed, via = cli.get("/api/verify?id=" + item_id, timeout=300)
        if via != "live" or not isinstance(observed, dict) or observed.get("item") != item_id:
            return {"status": "unknown", "detail": f"live detector unavailable ({via}) at {cli.URL}"}
        return observed.get("detector") or {}

    results = apply(model, evidence, a.repo, a.events, observe, derived)
    print(json.dumps(results, indent=1, default=str) if a.json else "\n".join(
        (f"CLOSED  {r['item']}" if r["closed"] else f"REFUSED {r['item']}: {r['refused']}") for r in results))
    return 0 if all(r["closed"] for r in results) else 3


if __name__ == "__main__":
    raise SystemExit(main())
