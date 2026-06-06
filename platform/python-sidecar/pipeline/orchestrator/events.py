"""Event emission — Pub/Sub in Phase 4; stdout stub for now."""
from __future__ import annotations

import json
import os
import sys


def emit_event(event: dict) -> None:
    if os.environ.get("PUBSUB_DISABLED") or not os.environ.get("PUBSUB_TOPIC"):
        print(f"[event] {json.dumps(event)}", flush=True)
        return
    _pubsub_publish(event)


def _pubsub_publish(event: dict) -> None:
    """Fire-and-forget publish to cockpit-events Pub/Sub topic (Phase 4 wired)."""
    try:
        from google.cloud import pubsub_v1

        project = os.environ.get("GCP_PROJECT", "madhav-astrology")
        topic_id = os.environ.get("PUBSUB_TOPIC", "cockpit-events")

        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(project, topic_id)
        data = json.dumps(event).encode("utf-8")
        attrs = {
            "chart_id": str(event.get("chart_id", "")),
            "type": event["type"],
        }
        future = publisher.publish(topic_path, data, **attrs)
        future.add_done_callback(_on_done)
    except Exception as exc:
        print(f"[pubsub-error] {exc}", file=sys.stderr, flush=True)


def _on_done(future) -> None:
    try:
        future.result(timeout=5)
    except Exception as exc:
        print(f"[pubsub-publish-error] {exc}", file=sys.stderr, flush=True)
