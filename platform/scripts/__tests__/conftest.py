"""conftest: the no-real-cloud guard (see platform/scripts/governance/no_real_cloud_guard.py)."""
from __future__ import annotations

# --- no test may launch a real cloud command (2026-10-05 incident): installed at conftest import, see platform/scripts/governance/no_real_cloud_guard.py ---
import pathlib as _pl
import sys as _sys
for _p in _pl.Path(__file__).resolve().parents:
    for _cand in (_p / "scripts" / "governance", _p / "platform" / "scripts" / "governance"):
        if (_cand / "no_real_cloud_pytest.py").exists():
            _sys.path.insert(0, str(_cand))
            break
    else:
        continue
    break
from no_real_cloud_pytest import *  # noqa: E402,F401,F403  (an ImportError here must stay loud: no silent disabling)
