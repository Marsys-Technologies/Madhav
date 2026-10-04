#!/usr/bin/env python3
"""Writes plan.txt (the exact text the plan hash covers) and prints the executor sha256 and both plan hashes (unbound, and bound to the GATE_V2
pins). Re-run it after ANY edit of the executor, the sql or the verify files; the plan hash changes with every one of them."""
import importlib.util
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("l5_frozen_guard_exec", HERE / "l5_frozen_guard_exec.py")
ex = importlib.util.module_from_spec(spec)
sys.modules["l5_frozen_guard_exec"] = ex
spec.loader.exec_module(ex)

ex.verify_sql_bodies()
text = ex.render_plan()
(HERE / "plan.txt").write_text(text + "\n\n-- EXPECTED_DIFF\n" + json.dumps(ex.expected_diff(), indent=1, sort_keys=True) + "\n")
print(json.dumps({"executor_sha256": ex.exec_sha(), "plan_hash_unbound": ex.plan_hash_unbound(), "plan_hash_bound": ex.plan_hash(),
                  "forward_sql_sha256": ex.sha_file(ex.FORWARD_SQL), "rollback_sql_sha256": ex.sha_file(ex.ROLLBACK_SQL)}, indent=2))
