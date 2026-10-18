"""conftest for the fleet tests: no test's git may act on a repository the test did not create.

Incident (2026-10-17 02:09Z): pytest was started with GIT_DIR=<a linked worktree's gitdir> exported. The World fixture's `git init --bare` honoured it (GIT_DIR beats `-C`)
and re-initialised the SHARED repository as bare, taking every worktree down. The repository-locating variables are removed from the process environment at conftest import,
before any test module builds its git environment from os.environ. Tests that exercise GIT_DIR handling pass it in an explicit env at test time, which this does not touch.
GIT_CEILING_DIRECTORIES stays: it can only stop upward discovery, never redirect git. Same list as platform/scripts/governance/git_env_scrub.py (the fleet stays self-contained).
"""
import os

GIT_REPO_LOCATING_VARS = ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE",
                          "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_NAMESPACE")

for _name in GIT_REPO_LOCATING_VARS:
    os.environ.pop(_name, None)
