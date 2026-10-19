"""A code item is done when its PR is merged AND contained in a successful deploy of main (SR-BOLD-07).

The PR's merged review is the item's acceptance: no per-item verdict event, no post-deploy verdict, no `review`
limbo. `derive` is a pure function of the plan model and a `Source` (the observations); `GitHubSource` reads them
from `gh` and local git only (no new credential) and `CodeDone` runs it off the tick path, so a request or a tick
never waits on an external call. Operation items still close from executor receipts and decisions from the ledger
(state.item_status); only declared `completion_kind: code` items with a PR-shaped detector are derived here.

Item -> PR, in this order (a PR from an earlier step is never replaced by a later one):
1. the PR the plan model names: `detector.pr`, `detector.packet_pr`, or the PR that squash-merged `detector.ref`
   when that is a commit; a bundle child names its bundle's PR here;
2. otherwise a `detector.ref` branch: the merged PR whose head branch it is.
An item with neither is not derived: no PR on main is guessed from the files an item owns (an old PR that touched
the same files is not the item's acceptance). A bundle child names its bundle's PR in the plan model (step 1).
A PR must also carry the item (it is a bundle): at least one owned path in its diff and every owned path
present in its merged tree (an owned file that an earlier merged PR already landed is still there).
"""
from __future__ import annotations

import collections
import json
import re
import subprocess
import threading
import time

from . import detectors as D

DEPLOY_WORKFLOW = "Deploy to Cloud Run"
SOURCE = "derived:merged+deployed"
REFRESH_S = 60.0           # how often the background refresh re-reads GitHub and git
MERGED_LIST_LIMIT = 300    # one `gh pr list` call maps head branches of the newest merged PRs

_SHA = re.compile(r"[0-9a-f]{40}")
_SQUASH_SUBJECT = re.compile(r"\(#(\d+)\)\s*$")


def _number(value) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else None


def _sha(value) -> bool:
    return isinstance(value, str) and _SHA.fullmatch(value) is not None


def _owns(item: dict) -> list[str]:
    brief = item.get("brief") if isinstance(item.get("brief"), dict) else {}
    owns = brief.get("owns")
    return [p for p in owns if isinstance(p, str) and p] if isinstance(owns, list) else []


def is_derivable(item: dict) -> bool:
    """A declared code item whose detector names a PR or a branch/commit of main (not a file, DB or HTTP probe)."""
    detector = item.get("detector") if isinstance(item.get("detector"), dict) else {}
    return (item.get("completion_kind") == "code" and item.get("done_by") not in ("decision", "join")
            and not item.get("join") and detector.get("type") in ("pr_merged", "branch_merged"))


def named_prs(item: dict, source) -> list[int]:
    """Step 1: the PRs the plan model names for the item, in declaration order, without repeats."""
    detector = item["detector"]
    found: list[int] = []
    for number in (_number(detector.get("pr")), _number(detector.get("packet_pr"))):
        if number is not None and number not in found:
            found.append(number)
    ref = detector.get("ref")
    if _sha(ref):
        number = source.pr_of_commit(ref)
        if number is not None and number not in found:
            found.append(number)
    return found


def _carries(item: dict, source, merge: str) -> bool:
    owns = _owns(item)
    diff = source.diff_paths(merge)
    if diff is None:
        return False
    if not owns:
        return True            # nothing to compare: the PR the plan model names stands for the item
    return any(p in diff for p in owns) and all(source.has_path(merge, p) for p in owns)


def _proof(number: int, pr: dict, merge: str, deploy: dict) -> dict:
    return {"pr": number, "head": pr.get("headRefOid"), "merge_commit": merge,
            "deployed_sha": deploy["deployed_sha"], "deploy_run_id": deploy["run_id"],
            "detail": f"PR #{number} merged ({merge[:9]}) and contained in deploy run {deploy['run_id']}",
            "evidence": (f"PR #{number} merged {merge}; deployed {deploy['deployed_sha']} "
                         f"(run {deploy['run_id']}) contains the merge commit; the PR's merged review is the acceptance")}


def _accepted(item: dict, source, number: int) -> dict | None:
    """The proof when PR `number` is merged, carries the item and is contained in a successful main deploy."""
    pr = source.pr(number)
    if not isinstance(pr, dict) or pr.get("state") != "MERGED":
        return None
    commit = pr.get("mergeCommit") if isinstance(pr.get("mergeCommit"), dict) else {}
    merge = commit.get("oid")
    if not _sha(merge) or not _carries(item, source, merge):
        return None
    deploy = source.deployed(merge)
    if (not isinstance(deploy, dict) or deploy.get("contains_merge") is not True or not deploy.get("run_id")
            or not _sha(deploy.get("deployed_sha"))):
        return None
    return _proof(number, pr, merge, deploy)


def derive_item(item: dict, source) -> dict | None:
    named = named_prs(item, source)
    candidates = list(named)
    if not candidates:
        ref = item["detector"].get("ref")
        branch = ref.split("/", 1)[1] if isinstance(ref, str) and ref.startswith("origin/") else None
        if branch:
            candidates = list(source.merged_prs_for_branch(branch))
    for number in candidates:
        proof = _accepted(item, source, number)
        if proof:
            return proof
    return None


def derive(model: dict, source, *, skip=frozenset()) -> dict[str, dict]:
    """item id -> proof, for every derivable code item (not in `skip`) that is merged and deployed."""
    out: dict[str, dict] = {}
    for item in model.get("items", []):
        if item.get("id") in skip or not is_derivable(item):
            continue
        try:
            proof = derive_item(item, source)
        except (subprocess.SubprocessError, OSError):
            continue    # one slow or failing call leaves that item undecided for this pass, never the others
        if proof:
            out[item["id"]] = proof
    return out


def completed_by_event(events: list[dict]) -> set:
    """Items a guarded done event already closed: the derivation need not look at them (they win in item_status)."""
    return {e.get("item") for e in events
            if e.get("kind") == "item" and e.get("state") == "done" and not e.get("step") and e.get("guarded") is True}


def upstream_ids(model: dict, item_id: str) -> set:
    """`item_id` and every item it transitively depends on."""
    by_id = {i.get("id"): i for i in model.get("items", [])}
    seen, todo = set(), [item_id]
    while todo:
        iid = todo.pop()
        if iid in seen:
            continue
        seen.add(iid)
        todo.extend(by_id.get(iid, {}).get("depends_on", []))
    return seen


def derive_for_events(model: dict, events: list[dict], source, *, only=None) -> dict[str, dict]:
    """The merged+deployed `derived_done` map exactly as the display computes it (server.py): the one derivation
    every completion predicate shares. `only` limits the work to those item ids (a completion needs just the
    item and its upstream); the proofs are the same ones the full pass would give."""
    skip = completed_by_event(events)
    if only is not None:
        skip |= {i.get("id") for i in model.get("items", []) if i.get("id") not in only}
    return derive(model, source, skip=skip)


class GitHubSource:
    """Observations from `gh` and local git, cached: git facts about a commit never change, a merged PR stays
    merged, and a deploy that contains a commit keeps containing it. Everything else is re-read after REFRESH_S."""

    def __init__(self, repo: str):
        self.repo = repo
        self._lock = threading.Lock()
        self._prs: dict[int, tuple[float, dict | None]] = {}
        self._heads: dict[str, list[int]] = {}
        self._diffs: dict[str, frozenset] = {}
        self._paths: dict[tuple[str, str], bool] = {}
        self._subjects: dict[str, int | None] = {}
        self._contained: dict[str, dict] = {}
        self._not_contained: dict[str, float] = {}
        self._runs: tuple[float, list[dict]] | None = None
        self._main: str | None = None

    def _call(self, cmd: list[str]) -> tuple[int, str]:
        """A refresh step that times out or cannot start is a failed step (exit 124), not a failed pass."""
        try:
            return D._run(cmd, cwd=self.repo)
        except (subprocess.SubprocessError, OSError) as exc:
            return 124, type(exc).__name__

    # -- one pass --------------------------------------------------------------------------------
    def refresh(self) -> None:
        """Re-read what can change: main, the merged-PR list and the deploy runs. Failures keep the last values."""
        with self._lock:
            self._runs = None
            self._not_contained.clear()
            self._prs = {n: v for n, v in self._prs.items() if v[1] and v[1].get("state") == "MERGED"}
        self._call(["git", "fetch", "-q", "origin", "main"])
        rc, out = self._call(["git", "rev-parse", "origin/main"])
        with self._lock:
            self._main = out.strip() if rc == 0 else self._main
        rc, out = self._call(["gh", "pr", "list", "--state", "merged", "--base", "main", "--limit",
                              str(MERGED_LIST_LIMIT), "--json", "number,state,headRefName,headRefOid,mergeCommit"])
        if rc == 0:
            heads: dict[str, list[int]] = collections.defaultdict(list)
            for pr in _json_list(out):
                if _number(pr.get("number")) is not None:
                    with self._lock:
                        self._prs[pr["number"]] = (time.time(), pr)
                    heads[str(pr.get("headRefName"))].append(pr["number"])
            with self._lock:
                self._heads = dict(heads)

    # -- Source ----------------------------------------------------------------------------------
    def pr(self, number: int) -> dict | None:
        with self._lock:
            cached = self._prs.get(number)
        if cached is not None:
            return cached[1]
        rc, out = D._run(["gh", "pr", "view", str(number), "--json", "number,state,headRefName,headRefOid,mergeCommit"],
                         cwd=self.repo)
        try:
            pr = json.loads(out) if rc == 0 else None
        except ValueError:
            pr = None
        pr = pr if isinstance(pr, dict) else None
        if pr is not None:
            with self._lock:
                self._prs[number] = (time.time(), pr)
        return pr

    def merged_prs_for_branch(self, branch: str) -> list[int]:
        with self._lock:
            return list(self._heads.get(branch, []))

    def pr_of_commit(self, sha: str) -> int | None:
        with self._lock:
            if sha in self._subjects:
                return self._subjects[sha]
        rc, out = D._run(["git", "log", "-1", "--format=%s", sha], cwd=self.repo)
        match = _SQUASH_SUBJECT.search(out.strip()) if rc == 0 else None
        number = int(match.group(1)) if match else None
        if rc == 0:
            with self._lock:
                self._subjects[sha] = number
        return number

    def diff_paths(self, merge: str) -> frozenset | None:
        with self._lock:
            if merge in self._diffs:
                return self._diffs[merge]
        rc, out = D._run(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "--first-parent", merge],
                         cwd=self.repo)
        if rc != 0:
            return None
        paths = frozenset(line for line in out.splitlines() if line)
        with self._lock:
            self._diffs[merge] = paths
        return paths

    def has_path(self, merge: str, path: str) -> bool:
        with self._lock:
            if (merge, path) in self._paths:
                return self._paths[(merge, path)]
        rc, _ = D._run(["git", "cat-file", "-e", f"{merge}:{path}"], cwd=self.repo)
        with self._lock:
            self._paths[(merge, path)] = rc == 0
        return rc == 0

    def deployed(self, merge: str) -> dict:
        """A successful `workflow_run` deploy of main whose sha contains `merge` (cli.observe_containment's rule)."""
        none = {"deployed_sha": None, "run_id": None, "contains_merge": False}
        with self._lock:
            if merge in self._contained:
                return self._contained[merge]
            if merge in self._not_contained:
                return none
        runs = self._deploy_runs()
        if runs is None:
            return none
        for run in runs:
            if not isinstance(run, dict) or run.get("event") != "workflow_run" or not _sha(run.get("headSha")):
                continue
            rc, _ = D._run(["git", "merge-base", "--is-ancestor", merge, run["headSha"]], cwd=self.repo)
            if rc == 0:
                found = {"deployed_sha": run["headSha"], "run_id": run.get("databaseId"), "contains_merge": True}
                with self._lock:
                    self._contained[merge] = found
                return found
        with self._lock:
            self._not_contained[merge] = time.time()
        return none

    def _deploy_runs(self) -> list[dict] | None:
        with self._lock:
            if self._runs is not None:
                return self._runs[1]
        rc, out = D._run(["gh", "run", "list", "--workflow", DEPLOY_WORKFLOW, "--branch", "main", "--status", "success",
                          "--limit", "15", "--json", "databaseId,headSha,event,createdAt"], cwd=self.repo)
        if rc != 0:
            return None
        runs = _json_list(out)
        with self._lock:
            self._runs = (time.time(), runs)
        return runs


def _json_list(text: str) -> list[dict]:
    try:
        value = json.loads(text or "[]")
    except ValueError:
        return []
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []


class CodeDone:
    """Runs `derive` in one background thread at most every REFRESH_S; readers get the last complete result.

    Nothing here blocks the tick or a request: `poll` only starts the worker, every external call inside it has
    detectors._run's per-call timeout, and a failed pass keeps the previous result (a merge cannot un-happen; the
    snapshot is not allowed to flip a done item back because GitHub was slow).
    """

    def __init__(self, repo: str, sources=None, on_change=None, source=None):
        self.source = source or GitHubSource(repo)
        self.sources = sources
        self.on_change = on_change or (lambda: None)
        self._lock = threading.Lock()
        self._result: dict[str, dict] = {}
        self._due = 0.0
        self._running = False
        self.error: str | None = None

    def results(self) -> dict[str, dict]:
        with self._lock:
            return dict(self._result)

    def due(self) -> bool:
        with self._lock:
            return not self._running and time.time() >= self._due

    def poll(self, model: dict, skip=frozenset()) -> bool:
        """Start a refresh when due; returns whether one was started."""
        with self._lock:
            if self._running or time.time() < self._due:
                return False
            self._running = True
        threading.Thread(target=self._work, args=(model, frozenset(skip)), name="code-done", daemon=True).start()
        return True

    def run_once(self, model: dict, skip=frozenset()) -> None:
        """One synchronous pass (the worker body; tests call it directly)."""
        with D.external_context(self.sources):
            if hasattr(self.source, "refresh"):
                self.source.refresh()
            fresh = derive(model, self.source, skip=skip)
        with self._lock:
            changed = {k: v["deploy_run_id"] for k, v in fresh.items()} != \
                      {k: v["deploy_run_id"] for k, v in self._result.items()}
            # a pass that could not reach GitHub finds fewer items; never let it un-derive a done item
            self._result = {**self._result, **fresh}
            self.error = None
        if changed:
            self.on_change()

    def _work(self, model: dict, skip) -> None:
        try:
            self.run_once(model, skip)
        except (subprocess.SubprocessError, OSError, ValueError) as exc:
            with self._lock:
                self.error = f"{type(exc).__name__}: {exc}"[:200]
        finally:
            with self._lock:
                self._running = False
                self._due = time.time() + REFRESH_S
