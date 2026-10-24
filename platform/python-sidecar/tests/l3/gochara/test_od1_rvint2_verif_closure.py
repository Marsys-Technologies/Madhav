"""RV-INT part 2, VERIF-CLOSURE — every gochara module the VERIFICATION JOB imports sits in an implementation stage list.

`test_a53_input_vector.py::test_the_implementation_stage_lists_cover_the_writers_import_closure` follows the WRITER's imports only. The verification job (the in-build / sealed re-derivation,
`pipeline.orchestrator.verification_job`) imports kernel modules the writer does not (R8X's `g6_plan` joined the window list by hand at the 3b merge). A module on that path that is in no
stage list can be edited without moving the input vector, so a changed re-derivation would leave every pin standing (root CLAUDE.md §N.8: a signal whose check cannot read false is null).

Fail-on-revert (ONE): `input_vector.IMPLEMENTATION_MODULES["window"]` without `g6_plan` (`"verification_job", "g6_plan", "window_gate"` -> `"verification_job", "window_gate"`); the
writer-closure test stays green under it. Source: brief §2.3 / §2.11, TRIAL_READY T19."""
from __future__ import annotations

from services.gochara_kernel import input_vector as iv

from ._import_closure import writer_closure


def test_verif_closure_every_module_the_verification_job_imports_is_in_a_stage_list():
    listed = {m for mods in iv.IMPLEMENTATION_MODULES.values() for m in mods}
    closure = writer_closure(root="pipeline.orchestrator.verification_job")
    assert {"services.gochara_kernel.g6_plan", "services.gochara_kernel.window_cert_check"} <= closure       # the helper really walks the job's imports
    assert closure - listed == set(), sorted(closure - listed)
