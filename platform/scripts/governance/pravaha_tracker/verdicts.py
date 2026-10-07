"""Independent verdict lookup at the exact reviewed head or artifact digest."""
from __future__ import annotations


def accepted_verdict(events: list[dict], item: str, *, head: str | None = None,
                     artifact_digest: str | None = None, phase: str = "pre_merge") -> dict | None:
    """Return the latest ACCEPTED verdict only when its identity still matches.

    A later rejection at the same identity revokes acceptance. A new PR head has
    a different identity and therefore cannot inherit an older verdict.
    """
    if bool(head) == bool(artifact_digest):
        return None
    latest = next((event for event in reversed(events)
                   if event.get("kind") == "verdict" and event.get("item") == item
                   and event.get("phase") == phase
                   and event.get("head") == head
                   and event.get("artifact_digest") == artifact_digest), None)
    return latest if latest and latest.get("result") == "ACCEPTED" else None
