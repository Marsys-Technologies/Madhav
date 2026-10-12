"""Independent verdict lookup at the exact reviewed head or artifact digest."""
from __future__ import annotations


def _inherits(repo: str, old_head: str, new_head: str) -> bool:
    """Ask the ONE inheritance predicate (relaunch plan v2.7 §6), shared with the dispatcher: top-level module
    `kyverdicts`, put on sys.path by the `ky` wrapper and the tracker service (`<root>/fleet_live`).

    Fail-closed: no module, an exception or any answer other than True inherits nothing.
    """
    try:
        import kyverdicts
        return kyverdicts.inherits(repo, old_head, new_head) is True
    except Exception:  # noqa: BLE001
        return False


def accepted_verdict(events: list[dict], item: str, *, head: str | None = None,
                     artifact_digest: str | None = None, phase: str = "pre_merge",
                     repo: str | None = None) -> dict | None:
    """Return the latest ACCEPTED verdict only when its identity still matches.

    A later rejection at the same identity revokes acceptance. A new PR head has a different identity
    and cannot inherit an older verdict — except (pre_merge only, `repo` given) when the shared
    reviewed-patch predicate proves that the reviewed patch is unchanged at the new head.
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
                if event.get("result") == "ACCEPTED" and _inherits(repo, event["head"], head):
                    return event
                return None
    return None
