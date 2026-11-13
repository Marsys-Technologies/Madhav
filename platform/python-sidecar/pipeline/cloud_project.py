"""Pure project-binding compatibility shared by packaged pipeline readers."""
from __future__ import annotations

from typing import Mapping


def read_google_cloud_project(
    env: Mapping[str, str | None], default: str | None = None
) -> str | None:
    """Resolve the canonical project, preserving empty values and caller defaults."""
    project = env.get("GOOGLE_CLOUD_PROJECT")
    return default if project is None else project
