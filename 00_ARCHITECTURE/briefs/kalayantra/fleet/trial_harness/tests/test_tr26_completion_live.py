"""TR-26 G-completion, LIVE (opt-in: KY_COMPLETION_LIVE=1; ~4 minutes, the local lane cluster and the approved canonical-L1 export): `trial_slice.py completion-probe` end to end at the checkout.

What it proves, with the writer AS IT IS at the checkout (it must not assert the writer's pin state — the writer fix lands in another lane):
  * the build really went through `asset_runner.run_asset` and wrote its receipt: the provenance check reads TRUE, with the expected_code_digest computed by a separate interpreter;
  * the horizon_basis check is a faithful function of the stored manifest: TRUE exactly when the century-shaped manifest carries the pin, FALSE (not an error, not NULL) when it does not — at the
    H2 writer the manifest carries none and the check reads FALSE, the very shape the century run read (status candidate, stored_scope stored_non_moon, horizon_basis null)."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import completion as cp
import gates

HARNESS = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(os.environ.get("KY_COMPLETION_LIVE") != "1", reason="live completion probe: set KY_COMPLETION_LIVE=1 (about 4 minutes)")


def test_the_live_completion_probe_reads_the_real_entry_receipt_true_and_the_manifest_pin_faithfully(tmp_path):
    checkout = Path(os.environ["KY_TEST_CHECKOUT"])
    out = tmp_path / "cp"
    p = subprocess.run([sys.executable, "-I", "-X", "utf8", str(HARNESS / "trial_slice.py"), "completion-probe", "--checkout", str(checkout), "--out", str(out), "--slice-days", "30"],
                       capture_output=True, text=True, timeout=1500)
    rec = json.loads((out / "completion.json").read_text())
    assert rec["schema"] == cp.SCHEMA and rec["entry"].startswith("pipeline.orchestrator.asset_runner.run_asset")
    got = cp.evaluate_record(rec, rec["ruled_horizon"])
    assert got["provenance"][0] is True, (got, p.stderr[-500:])
    cell = json.loads(rec["horizon_basis"]["readback"])
    assert cell["status"] == "candidate" and cell["stored_scope"] == "stored_non_moon" and cell["test_slice"] is None
    assert got["horizon_basis"][0] is (isinstance(cell["horizon_basis"], dict) and bool(cell["horizon_basis"]) and cell["horizon_basis"].get("schema") == cp.BASIS_SCHEMA)
    rows = [r for r in rec["provenance"]["receipts"]]
    assert rows and all(r["build_id"] == rec["provenance"]["run_id"] and r["code_digest"] == rec["provenance"]["expected_code_digest"] for r in rows)
