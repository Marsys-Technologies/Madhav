"""Independent verdict lookup at the exact reviewed head or artifact digest."""
from __future__ import annotations


def merge_only_between(repo: str | None, old_head: str, new_head: str) -> bool:
    """True when every commit in old_head..new_head is a merge commit (the branch only took main in).

    Velocity amendment §5: such a push does not change the reviewed diff, so the verdict at old_head stays
    current. Any failure to answer (no repo, unknown commits) is False — a verdict is never inherited by guess.
    """
    import re as _re, subprocess
    if not repo or old_head == new_head:
        return old_head == new_head
    if not (_re.fullmatch(r"[0-9a-f]{40}", old_head or "") and _re.fullmatch(r"[0-9a-f]{40}", new_head or "")):
        return False
    try:
        anc = subprocess.run(["git", "merge-base", "--is-ancestor", old_head, new_head], cwd=repo,
                             capture_output=True, text=True, timeout=30)
        if anc.returncode != 0:
            return False
        # merging main INTO the branch brings main's own (non-merge) commits along; what must be empty is the set of
        # NON-merge commits added to the branch since old_head that main does not already carry
        main_ref = next((r for r in ("origin/main", "main")
                         if subprocess.run(["git", "rev-parse", "--verify", "-q", r], cwd=repo,
                                           capture_output=True, timeout=30).returncode == 0), None)
        if not main_ref:
            return False
        out = subprocess.run(["git", "rev-list", "--no-merges", f"{old_head}..{new_head}", f"^{main_ref}"], cwd=repo,
                             capture_output=True, text=True, timeout=30, check=True)
    except (OSError, subprocess.SubprocessError):
        return False
    return out.stdout.strip() == ""


def accepted_verdict(events: list[dict], item: str, *, head: str | None = None,
                     artifact_digest: str | None = None, phase: str = "pre_merge",
                     repo: str | None = None) -> dict | None:
    """Return the latest ACCEPTED verdict only when its identity still matches.

    A later rejection at the same identity revokes acceptance. A new PR head has a different identity
    and cannot inherit an older verdict — except (amendment §5, pre_merge only, `repo` given) when the
    only commits since the verdict's head are merge commits, which leave the reviewed diff unchanged.
    """
    if bool(head) == bool(artifact_digest):
        return None
    latest = next((event for event in reversed(events)
                   if event.get("kind") == "verdict" and event.get("item") == item
                   and event.get("phase") == phase
                   and event.get("head") == head
                   and event.get("artifact_digest") == artifact_digest), None)
    if latest:
        return latest if latest.get("result") == "ACCEPTED" else None
    if head and repo and phase == "pre_merge":
        for event in reversed(events):
            if (event.get("kind") == "verdict" and event.get("item") == item and event.get("phase") == phase
                    and event.get("head") and event.get("artifact_digest") is None):
                # the latest verdict of this item at any head decides; a rejection there is not inherited either
                if event.get("result") == "ACCEPTED" and merge_only_between(repo, event["head"], head):
                    return event
                return None
    return None
