"""Strip the variables that decide WHICH repository git acts on, so a test fixture's git can only touch the repository the fixture made.

Incident (2026-10-17 02:09Z): pytest was started with GIT_DIR=<a linked worktree's gitdir>. A fixture ran `git init --bare <tmp>`; git honoured the inherited GIT_DIR
(it beats `-C`) and re-initialised the SHARED repository as bare (core.bare=true), taking every worktree down. Importing this module (a conftest does it through
no_real_cloud_pytest) removes the variables from the process environment, so every helper that inherits os.environ is safe, now and in future.

GIT_CEILING_DIRECTORIES is left alone on purpose: it can only stop upward repository discovery, it cannot point git at another repository.
"""
from __future__ import annotations

import os

REPO_LOCATING_VARS = (
    "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_NAMESPACE",
)


def scrubbed(env=None) -> dict:
    """A copy of `env` (default: os.environ) without the repository-locating variables."""
    return {k: v for k, v in (os.environ if env is None else env).items() if k not in REPO_LOCATING_VARS}


def scrub_process_env() -> None:
    for name in REPO_LOCATING_VARS:
        os.environ.pop(name, None)


scrub_process_env()
