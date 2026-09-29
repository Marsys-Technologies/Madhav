#!/usr/bin/env python3
"""E-020 gate-(b) instrumented step06b runner (ADK-0026 §3(iii)).

Runs the REAL step06b main() in-process (same argv as the production-shape
invocation), with the writer's `_window_row` wrapped so every window row's
enter/exit/peak JD is ALSO dated under the pre-fix noon-UTC convention
(int(jd - 2440588.0)). Each row where the two conventions differ is logged to
a JSONL shift ledger with the underlying instant's UTC time-of-day, giving the
native's falsifiable gate-(b) rule an exact window-level evaluation:

    every corrected '4.0' date that differs from the old convention must
    differ by EXACTLY +1 day, and only when the underlying instant's UTC
    time-of-day is in [00:00, 12:00).

The wrapper returns the original row unchanged — the written projection is
identical to an uninstrumented run (the wrapper observes; it never alters).
The contact-level half of the gate is evaluated separately and exhaustively
over all '4.0' ledger contacts in the evidence SQL (t_exact instants).
"""
from __future__ import annotations

import importlib.util
import json
import sys
from datetime import date, timedelta
from pathlib import Path

SIDECAR = Path(__file__).resolve().parents[3]
WRITER_PATH = SIDECAR / "scripts/kala_gochara_cutover/step06b_windows_projection.py"


def old_convention_date(jd: float) -> date:
    """The pre-E-020 convention, verbatim: date(1970,1,1) + int(jd - 2440588.0)."""
    return date(1970, 1, 1) + timedelta(days=int(jd - 2440588.0))


def main() -> int:
    out_path = sys.argv.pop(1)  # shift ledger JSONL out
    spec = importlib.util.spec_from_file_location("step06b_instrumented", WRITER_PATH)
    w = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = w
    spec.loader.exec_module(w)

    orig_window_row = w._window_row
    ledger_f = open(out_path, "w")

    def observing_window_row(class_ctx, evaluate, *, window_key, parent_key,
                             tier, enter_jd, exit_jd, peak_jd):
        row = orig_window_row(class_ctx, evaluate, window_key=window_key,
                              parent_key=parent_key, tier=tier,
                              enter_jd=enter_jd, exit_jd=exit_jd, peak_jd=peak_jd)
        for field, jd in (("window_start", enter_jd), ("window_end", exit_jd),
                          ("peak_date", peak_jd)):
            old_d = old_convention_date(jd)
            new_d = w.date_of_jd(jd)
            if old_d != new_d:
                tod_hours = ((jd - 2440587.5) % 1.0) * 24.0
                ledger_f.write(json.dumps({
                    "event_class": class_ctx.event_class, "tier": tier,
                    "field": field, "jd": jd, "old_date": old_d.isoformat(),
                    "new_date": new_d.isoformat(),
                    "shift_days": (new_d - old_d).days,
                    "utc_time_of_day_hours": round(tod_hours, 6),
                }) + "\n")
        return row

    w._window_row = observing_window_row
    rc = w.main()
    ledger_f.close()
    return rc


if __name__ == "__main__":
    sys.exit(main())
