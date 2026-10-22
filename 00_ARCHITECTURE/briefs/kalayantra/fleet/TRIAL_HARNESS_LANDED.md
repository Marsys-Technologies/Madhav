# Trial harness v3.1 — landed in the repository (TR-BIND, 2026-10-22)

`fleet/trial_harness/` is a byte-for-byte copy of the accepted harness v3.1 (job `X-20261022T074412Z-t1b-fix`, review `X-20261022T075423Z-review-t1b-harness2`, ACCEPTED).
It was job-local until now; landing it makes the T14 and T17 checks of TRIAL_READY/1 bindable to `pytest` parts (the evaluator only runs oracles that exist at the evaluated commit).

- **Content digest** `efb0922aa74aaefb07b981fd019fa334301448a37d877536802657020569787c`: sha256 of the sorted `sha256sum`-style lines (`<hash>  ./<path>`) of every file, `__pycache__` excluded. The two `*.bak-*` files are part of the accepted deliverable and of the digest, so they stay. Pinned by `test_trial_ready.py::test_c12_*`: any edit fails it. A new harness version lands as a new reviewed digest, never as an edit.
- **Running its tests** (from this directory): `KY_TEST_CHECKOUT=<checkout holding platform/python-sidecar> python3 -m pytest tests -p no:cacheprovider --basetemp=<dir>`. The registry binds them with `KY_TEST_CHECKOUT={repo}`.
- **Known head-dependent test:** `tests/test_driver.py::test_probe_reports_absence_when_the_checkout_has_no_solver` asserts the checkout has NO `window_solver` (true of the SR-OD1 export it was written on). At any head that carries the solver (the integration head, main after merge-up) it reads false for a reason that is not a product claim, so the registry deselects exactly that node id (`deselect_why` in the T14 part). The positive probe test stays.
- **Not run by `ci.yml`:** the suite needs the integration code (solver, sweep primitives) that main does not carry yet; the TRIAL_READY evaluator runs it at the merged-up head.
