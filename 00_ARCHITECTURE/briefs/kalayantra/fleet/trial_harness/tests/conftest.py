import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HARNESS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HARNESS))
# the checkout whose sweep primitives the cross-check tests run against (a git-archive export of the SR-OD1 branch by default)
CHECKOUT = Path(os.environ.get("KY_TEST_CHECKOUT", HARNESS.parent / "code_od1"))
SIDECAR = CHECKOUT / "platform" / "python-sidecar"
if SIDECAR.is_dir():
    sys.path.insert(0, str(SIDECAR))
