"""
test_panchanga_native_context_kwarg.py — ṢAḌ-DARŚANA Gate W1 verify-reopen (items 29 + 32).

ROOT CAUSE B, guarded here at the exact layer it lived:
`routers/panchang.py::_fetch_native_context` called

    compute_panchang(birth_date, lat, lon, tz_offset_minutes=330)

while `panchang_engine.compute_panchang` declares its fourth parameter `tz_offset`. That raises
`TypeError: compute_panchang() got an unexpected keyword argument 'tz_offset_minutes'`, which the
surrounding `except (ValidationError, OutOfRangeError, PanchangEngineError)` does NOT catch — so
it escaped as an unhandled HTTP 500 out of `POST /api/compute/panchanga`.

`_fetch_native_context` is reached ONLY from the single-date endpoint AND only when `chart_id` is
supplied. That is precisely `kala_now_get`'s call shape (mode=single + chart_id) and precisely
NOT `kala_ahead_get`'s (mode=range, no chart_id) — which is why the range path served 31 real
per-day windows in the same session in which every single-date call failed, and why five
`kala_now_get` fields (disha_shula / gulika_kalam_now / chandrashtama / hora_now /
janma_resonance) were null on both canonical charts on every date tested.

These are STATIC (AST-level) and signature-level checks, deliberately requiring neither a live DB
nor a live sidecar, so they run in the default CI lane (`pytest -m "not integration"`) rather than
joining the never-runs-in-CI integration set. A defect of this class — a call that cannot possibly
succeed — is fully detectable without executing it, and a guard that never runs is itself the
CLAUDE.md §N.8 failure mode.
"""
import ast
import inspect
from pathlib import Path

import pytest

ROUTER_PATH = Path(__file__).resolve().parents[1] / "routers" / "panchang.py"


def _compute_panchang_calls_in_router():
    """Every `compute_panchang(...)` call site in routers/panchang.py, as AST nodes."""
    tree = ast.parse(ROUTER_PATH.read_text())
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "compute_panchang"
    ]


def test_router_has_compute_panchang_call_sites():
    """Guard the guard: if the scan finds nothing, the assertions below are vacuous (§N.8)."""
    calls = _compute_panchang_calls_in_router()
    assert len(calls) >= 3, f"expected >=3 compute_panchang call sites, found {len(calls)}"


def test_every_compute_panchang_call_matches_the_real_signature():
    """
    THE REOPENED DEFECT. Binds each call site's actual args/kwargs against the real
    `compute_panchang` signature via `inspect.Signature.bind`. A keyword-name mismatch
    (`tz_offset_minutes=` vs the declared `tz_offset`) fails here instead of at runtime as an
    HTTP 500 that silently blanks five unrelated served fields.
    """
    from panchang_engine import compute_panchang

    sig = inspect.signature(compute_panchang)
    calls = _compute_panchang_calls_in_router()

    for call in calls:
        kwarg_names = [kw.arg for kw in call.keywords if kw.arg is not None]
        # Positional args are represented by placeholders — only NAMES are being validated here.
        positional = ["<pos>"] * len(call.args)
        try:
            sig.bind(*positional, **{name: "<kw>" for name in kwarg_names})
        except TypeError as exc:
            pytest.fail(
                f"routers/panchang.py line {call.lineno}: compute_panchang"
                f"(*{len(call.args)} positional, **{kwarg_names}) does not match the real "
                f"signature {sig} — {exc}. This is ṢAḌ-DARŚANA Root Cause B: such a call raises "
                f"TypeError at runtime, which the router's "
                f"except (ValidationError, OutOfRangeError, PanchangEngineError) does not catch, "
                f"surfacing as an unhandled HTTP 500."
            )


def test_tz_offset_minutes_is_not_passed_as_a_keyword_to_compute_panchang():
    """Named, greppable regression guard for the exact wrong keyword."""
    for call in _compute_panchang_calls_in_router():
        names = [kw.arg for kw in call.keywords]
        assert "tz_offset_minutes" not in names, (
            f"routers/panchang.py line {call.lineno} passes tz_offset_minutes= to "
            f"compute_panchang; the engine's parameter is named tz_offset."
        )


def test_native_context_hydration_is_fail_soft_and_discloses_its_reason():
    """
    The hardening half. `native_context` is an OPTIONAL enrichment overlay, so a failure inside
    it must not destroy the already-computed panchāṅga payload — that coupling is how ONE
    keyword typo blanked five unrelated `kala_now_get` fields.

    Asserted structurally: the single-date endpoint must guard its `_fetch_native_context` call
    with a try/except AND must return a `native_context_error` key (an honest, attributable
    disclosure — never a silent null, per CLAUDE.md §N.8).
    """
    tree = ast.parse(ROUTER_PATH.read_text())

    endpoint = next(
        (
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "compute_panchanga_endpoint"
        ),
        None,
    )
    assert endpoint is not None, "compute_panchanga_endpoint not found in routers/panchang.py"

    guarded = [
        handler_parent
        for handler_parent in ast.walk(endpoint)
        if isinstance(handler_parent, ast.Try)
        and any(
            isinstance(inner, ast.Call) and getattr(inner.func, "id", None) == "_fetch_native_context"
            for inner in ast.walk(handler_parent)
        )
    ]
    assert guarded, (
        "_fetch_native_context is called OUTSIDE a try/except in compute_panchanga_endpoint — an "
        "optional overlay's failure would again propagate and destroy the whole panchāṅga payload."
    )

    returned_keys = {
        key.value
        for node in ast.walk(endpoint)
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict)
        for key in node.value.keys
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    }
    assert "native_context_error" in returned_keys, (
        "the single-date endpoint does not return `native_context_error` — an overlay failure "
        "would be an undisclosed silent null, and a consumer would have to guess whether the gap "
        "is transient unreachability or a deterministic defect (ND-4)."
    )
    assert "panchang" in returned_keys, "the panchāṅga payload itself must still be returned"
