"""RV-INT part 2 oracle N5-BOUND — claim: the certificate check's `"bound"` tolerance is the float4 interval (R67 lane review N-5), not a fixed 1e-6.

Doctrine / source: od1-r1 R-1 (`window_solver_check._f4_tol`: half a float4 spacing at the bound's magnitude + F4_ABS_SLACK) and GPT B2 (float4 class);
the FOLLOWUPS-137 merge edit changed TWO call sites of `window_cert_check._tol` (`bound` at the cell-witness check, `value` at the stored-value check). The lane's only
magnitude-aware oracle (test_od1_r67_certificate T-1) measures the `value` site; this file measures the `bound` site.

World: 33 roots each constant 0.97 -> sum 32.01 (the T-1 world). The certificate's one `piece` cell claims `sup F <= u`. A cell bound stored as a float4 is
float4(32.01) = 32.01 - 1.68e-6, i.e. the verifier's own evaluation (32.01) exceeds the claimed bound by 1.68e-6 — between the fixed 1e-6 and half a float4 spacing
at 32 (1.9e-6): a CORRECT certificate, so AGREED. The same cell bound 1e-3 low is a real violation: `certificate_bound_violated`.

Fail-on-revert (ONE): window_cert_check._tol `"bound"` branch `return chk._f4_tol(x)` -> `return chk.VALUE_TOL` (the whole of test_od1_r67_certificate.py stays green under it).
RV-INT part 2, finding F-2."""
from __future__ import annotations

import copy
import struct
from datetime import datetime, timedelta, timezone

from services.gochara_kernel import window_cert_check as cc
from services.gochara_kernel import window_solver as sol
from services.gochara_kernel import window_solver_check as chk

from .od1_solver_harness import member

T0 = datetime(2030, 1, 1, tzinfo=timezone.utc)


def at(s):
    return T0 + timedelta(seconds=s)


def _world():
    T, per_root = 2.0e5, 0.97
    sup = ((0.0, T),)
    res = sol.solve(sol.Problem(0.0, T, sol.OBJECTIVE_SUM, tuple(member(f"c{i}", f"r{i}", sup, steps=(sol.constant_step(per_root),)) for i in range(33))))
    cert = sol.stored_certificate(res, objective=sol.OBJECTIVE_SUM, t0_iso=T0.isoformat())
    recs = [chk.CheckRecord(f"c{i}", f"r{i}", f"B{i}", ((at(0), at(T)),), constant=per_root) for i in range(33)]
    stored = struct.unpack("f", struct.pack("f", res.value))[0]

    def check(c):
        return cc.check_numbered(lo=at(0), hi=at(T), records=recs, objective=chk.OBJ_SUM, stored=chk.StoredWindow(at(res.instant), stored),
                                 position_at=lambda body, d: 0.0, certificate=c)
    return res, cert, stored, check


def test_n5_bound_a_float4_stored_cell_bound_is_agreed_and_a_real_violation_is_not():
    res, cert, stored, check = _world()
    assert check(cert).classification == cc.AGREED
    assert cert["cells"][0][0] == "piece" and cert["cells"][0][3] == res.value
    gap = res.value - stored
    assert 1.2e-6 < gap < chk._f4_tol(res.value), "the world must sit between the fixed 1e-6 and half a float4 spacing"
    ok = copy.deepcopy(cert)
    ok["cells"][0][3] = stored                                   # the cell bound as a float4 round trip, 1.68e-6 below the verifier's evaluation
    rep = check(ok)
    assert rep.classification == cc.AGREED, (rep.classification, rep.findings)
    bad = copy.deepcopy(cert)
    bad["cells"][0][3] = stored - 1e-3                          # a bound the sky contradicts by 1e-3
    rep = check(bad)
    assert rep.classification == cc.DISAGREEMENT and [c for c, _ in rep.findings] == ["certificate_bound_violated"], (rep.classification, rep.findings)
