"""Pure project-binding compatibility shared by packaged pipeline readers."""
from __future__ import annotations

from typing import Mapping


def read_google_cloud_project(
    env: Mapping[str, str | None], default: str | None = None
) -> str | None:
    """Keep an explicit legacy binding, falling back only when it is absent."""
    project = env.get("GCP_PROJECT")
    if project is None:
        return env.get("GOOGLE_CLOUD_PROJECT", default)
    return project
