"""Keep routine GitHub Actions tests off the admission research cache."""

import os
import sys
from pathlib import Path

import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: protected admission-cache replay")
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return

    cache = (Path(__file__).resolve().parents[1] / "cache").resolve()
    config.pluginmanager.register(_CacheGuard(cache))


class _CacheGuard:
    def __init__(self, cache: Path):
        self.cache = cache
        self.denials = 0
        sys.addaudithook(self._check_open)

    def _check_open(self, event, args):
        if event != "open" or not isinstance(args[0], (str, bytes)):
            return

        path = Path(os.fsdecode(args[0])).resolve()
        if path.is_relative_to(self.cache):
            self.denials += 1
            raise PermissionError("admission research cache is unavailable in routine CI")

    def pytest_sessionfinish(self, session):
        if self.denials:
            session.exitstatus = pytest.ExitCode.TESTS_FAILED

    def pytest_terminal_summary(self, terminalreporter):
        if self.denials:
            terminalreporter.write_line(f"Admission research cache opens denied: {self.denials}", red=True)
