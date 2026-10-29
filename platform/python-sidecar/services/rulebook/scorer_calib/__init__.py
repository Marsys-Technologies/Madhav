"""Rule Book scorer calibration (yardstick v1.1 Part F): synthetic occurrences on chart timelines.

Library code for the step-5 calibration. It never reads an occurrence: occurrences here are SYNTHETIC,
placed by the pre-declared models N0-N4. Real timelines come from the engine driver run on birth data
only (see ``timelines``). Hashed separately from the scorer (``source_sha256``) as the simulator of F5.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

SIM_FILES = ("__init__.py", "births.py", "natal.py", "timelines.py", "occurrences.py", "harness.py", "cli.py")


def source_sha256() -> str:
    h = hashlib.sha256()
    here = Path(__file__).resolve().parent
    for name in SIM_FILES:
        p = here / name
        h.update(name.encode("utf-8") + b"\0" + (p.read_bytes() if p.exists() else b"<missing>") + b"\0")
    return h.hexdigest()
