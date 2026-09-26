#!/usr/bin/env python3.13
"""T1 mutation test: invert ONE comparison in a copy of asset_census.py and confirm
the planted suite notices.

Mutation: Vocab.identity verdict inverted (PASS<->FAIL on the duplicate count).
Protocol: plant the same Vocab.identity defect used by plant.py (duplicate rows under
the declared composite key of bg_sky_calendar), then run BOTH the original inspector
(control: must FAIL) and the mutant (must PASS — the plant assertion 'expect FAIL'
fails against the mutant, i.e. the suite notices the mutation).

Writes NT/harness/T1_MUTATION.json and prints a verdict line.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import plant  # noqa: E402

MUTANT = Path(__file__).parent / "asset_census_mutant.py"
OUT = Path(__file__).parent / "T1_MUTATION.json"

ORIGINAL = 'm["Vocab.identity"] = dict(v=(PASS if dup == "0" else FAIL),'
MUTATED = 'm["Vocab.identity"] = dict(v=(FAIL if dup == "0" else PASS),  # T1 MUTANT'


def make_mutant() -> None:
    src = plant.INSPECTOR.read_text()
    assert src.count(ORIGINAL) == 1, "mutation anchor not found exactly once"
    MUTANT.write_text(src.replace(ORIGINAL, MUTATED))


def main() -> int:
    make_mutant()
    ctx = plant.Ctx()
    vp = next(p for p in plant.PLANTS if p["id"] == "vocab_identity")
    res = dict(mutation="Vocab.identity PASS/FAIL inverted in asset_census_mutant.py",
               plant=vp["desc"], control_verdict=None, mutant_verdict=None,
               suite_notices=None, restore_ok=False, error=None)
    try:
        vp["plant"](ctx)
        control = plant.run_census("mutant_control_vocab_identity", layer="L4")
        mutant = plant.run_census("mutant_vocab_identity", layer="L4", script=MUTANT)
        res["control_verdict"] = plant.verdicts(control)["ph_sankrama"]["Vocab.identity"]
        res["mutant_verdict"] = plant.verdicts(mutant)["ph_sankrama"]["Vocab.identity"]
        res["control_measured"] = plant.measured(control, "ph_sankrama", "Vocab.identity")
        res["mutant_measured"] = plant.measured(mutant, "ph_sankrama", "Vocab.identity")
        # The suite's plant assertion is: planted defect => Vocab.identity == FAIL.
        # Control satisfies it, mutant violates it => the suite notices the mutation.
        res["suite_notices"] = (res["control_verdict"] == "FAIL"
                                and res["mutant_verdict"] != "FAIL")
    except Exception as exc:  # noqa: BLE001
        res["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        try:
            vp["restore"](ctx)
            res["restore_ok"] = bool(vp["verify"](ctx))
        except Exception as exc:  # noqa: BLE001
            res["error"] = (res["error"] or "") + f" | RESTORE {type(exc).__name__}: {exc}"
    OUT.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))
    return 0 if res["suite_notices"] and res["restore_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
