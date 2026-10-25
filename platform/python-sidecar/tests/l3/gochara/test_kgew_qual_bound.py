"""SR-KGEW-QUAL-BOUND — the ka_gochara_v5 solver certificate always fits `kgew_qualification_shape_ck` (century run 7b62d268, education_milestone P3).

The defects (proven on the pre-fix code): `window_solver._coarsen` never dropped `piece`/`leaf` cells, so a long window stored more than the 400 cells the database allows (901 -> 451;
the real record: 648 cells, 3,321 pieces); `stored_certificate` stored `geometry.cuts` / `geometry.pieces` unbounded, so ~4,000 elementary pieces exceeded `octet_length(c::text) <= 262144`
(the real worst case: 1,144 cells, 521,451 bytes). Migration 1402's shape is CLOSED and its caps are not raised (ruling: Option B rejected), so the writer fits the shape.

How a claim is tested (the repo's S2 / R67 pattern). Each claim has ONE oracle taking the modules under test (and, for a database claim, a real disposable database) and asserting what the
claim says, and ONE planted reversion `(module, old, new)` — a single textual change to that module's source that restores the pre-fix behaviour. `test_oracle_passes_on_the_real_code`
runs every oracle on the real modules; `test_the_single_planted_reversion_fails_the_oracle` loads a COPY of the source with that one change (it must match exactly once) and requires the
SAME oracle to fail. A claim whose reversion does not fail its oracle is a claim nothing measures (CLAUDE.md §N.8).

Synthetic inputs only (no chart value, no date is printed or stored); the database figures are measured on the REAL local cluster (the suite's own guarded fixture), never estimated.

Claims (the ruling item or classical/DB rule each oracle is built from):

  Q-1  cells are held to 400 whatever the tree: 901 cells -> <= 400, flagged truncated, the leaf bracket kept          ruling 1; 1402 `jsonb_array_length(cells) <= 400`
  Q-2  ~4,000 / ~6,000 pieces, and the real shapes (650 cells/3,300 pieces; 1,150 cells/~520 KB) store <= 262144 bytes
       as measured by the database, `ka_gochara_solver_certificate_ok` TRUE, digest over the FULL geometry              ruling 1/2; 1402 `octet_length(c::text) <= 262144`
  Q-3  the byte figure the builder fits to equals the database's `octet_length(c::text)` (jsonb text, not json.dumps)  ruling 1
  Q-4  the bounded form is FLAGGED: truncated true and `geometry.omitted` counts; a complete certificate is unflagged  ruling 2 (never a silent truncation)
  Q-5  the bounded geometry keeps every mixed and every sliver piece (the G-6 top-mixed rank and the sliver audit)     g6_plan.count_mixed; window_verifier sliver audit
  Q-6  a certificate that cannot fit even bounded raises `CertificateUnfit` (never an oversize certificate)            ruling 4
  Q-7  the sweep turns it into the named honest null `solver_certificate_incomplete`, no number, no certificate        ruling 4
  Q-8  the stored blank passes the FULL `kgew_qualification_shape_ck` in the database                                  ruling 4 (DB)
  Q-9  the pre-insert mirror agrees with the database's own rule on accept / refuse (cells, open, bytes, keys, types)  ruling 5
  Q-10 a pre-insert hit is a loud DEFECT naming the window key, before any row goes out (>400 cells; >256 KiB)         ruling 5/6 (DB)
  V-1  an incomplete certificate (truncated) is re-solved, never counted as certificate-checked                         ruling 3
  V-2  the stored geometry no longer hashing to `geometry_digest` is incomplete even when the flag says complete        ruling 3 / N.8 (a detector behind the flag)
  V-3  the verifier's budget running out on an incomplete certificate is INCONCLUSIVE (R-6), and the report says so     ruling 3
  V-4  a blank under `solver_certificate_incomplete` is INCONCLUSIVE at the verifier, not a disagreement               ruling 4 / R-6
  V-5  an incomplete certificate is re-solved from scratch, `run(None)`: the stored cells never seed the verifier's search  SR-KGEW-QUAL-BOUND-AMEND-3 (R-7, B-3)
"""
from __future__ import annotations

import copy
import functools
import hashlib
import json
import sys
import types
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from services.gochara_kernel import window_cert_check as cc
from services.gochara_kernel import window_solver as sol
from services.gochara_kernel import window_solver_check as chk
from services.gochara_kernel import window_store as wst
from services.gochara_kernel import window_sweep as ws
from services.gochara_kernel import window_verifier as wv

from .test_a53_inventory import create_am5_database, drop_am5_database
from .test_a53_record_store import (CHART, CHART_ID, MIGRATIONS,  # noqa: F401
                                    _coverage_kwargs, _grain_kwargs, _seed_saturn_crossings, _sky_convention_id)
from .test_a53_window_sweep_pg import GEN, T0 as PG_T0, _p3_probe, _qualification_manifest  # noqa: F401
from .test_od1_r67_certificate import Hump
from .test_od1_s3_integration import _p4_records, _solve

PKG = "services.gochara_kernel"
Q = sol.QUANT
M1402 = MIGRATIONS / "1402_gochara_qualification_provenance_certificate.sql"
CAP_BYTES = 262144


# ── synthetic trees: the shapes the century actually produced (counts only) ───────────────────────────────────────────────────────────────────────

def make_tree(n_pieces: int, n_cells: int, *, n_slivers: int = 0, n_mixed: int = 0, outcome: str = "solved", n_open: int = 0) -> dict:
    """A solved (or blank) tree with `n_pieces` elementary pieces (every `step`-th a sliver / mixed, the rest up/down) and `n_cells` closed cells (one `leaf`, the rest `piece`, never mergeable)."""
    cuts = [i * 3600.123456789 + 0.000123 for i in range(n_pieces + 1)]
    kinds = ["up" if i % 2 else "down" for i in range(n_pieces)]
    for k in range(n_slivers):
        kinds[(k * n_pieces) // max(1, n_slivers)] = "sliver"
    for k in range(n_mixed):
        i = (k * n_pieces) // max(1, n_mixed) + 1
        if i < n_pieces and kinds[i] != "sliver":
            kinds[i] = "mixed"
    pieces = [[cuts[i], cuts[i + 1] - Q, kinds[i]] for i in range(n_pieces)]
    cells = [["leaf" if k == 0 else "piece", k * 10.0, k * 10.0 + 5.0, 0.5 + k * 1e-7] for k in range(n_cells)]
    return {"outcome": outcome, "reason": None if outcome == "solved" else sol.REASON_BUDGET, "phase": "done", "value": 0.7 if outcome == "solved" else None,
            "instant": 12.5 if outcome == "solved" else None, "upper_bound": 0.7 if outcome == "solved" else None, "evals": 10, "max_evals": 100, "cuts": cuts,
            "pieces": pieces, "cells": cells, "open": [[k * 1.0, k * 1.0 + 0.5] for k in range(n_open)], "h4_used": False}


class _Result:
    def __init__(self, tree):
        self.tree = tree


def build(mods, tree, **kw):
    return mods["window_solver"].stored_certificate(_Result(tree), objective=sol.OBJECTIVE_SUM, t0_iso="2030-01-01T00:00:00+00:00", **kw)


def wrap(cert) -> dict:
    return {"policy": "window_qualification/1", "unqualified_reason": None, "unresolved": {}, "affected_channels": [], "members": 1, "qualified_members": 1,
            "solver_certificate": cert}


def db_figures(conn, cert) -> tuple:
    """(octet_length(c::text), ka_gochara_solver_certificate_ok(c)) as the REAL database computes them."""
    text = json.dumps(cert)
    return tuple(conn.execute("SELECT octet_length(%s::jsonb::text), public.ka_gochara_solver_certificate_ok(%s::jsonb)", (text, text)).fetchone())


def full_digest(tree) -> str:
    return hashlib.sha256(json.dumps({"cuts": tree["cuts"], "pieces": tree["pieces"]}, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


# ── the claims ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

CLAIMS: dict = {}


def claim(cid, module, old, new, *, db=False):
    def deco(fn):
        assert cid not in CLAIMS
        CLAIMS[cid] = (fn, module, old, new, db)
        return fn
    return deco


@claim("Q-1", "window_solver", "key=lambda c: (rank.get(c[0], 3), -(c[2] - c[1])))[:cap]",
       "key=lambda c: (rank.get(c[0], 3), -(c[2] - c[1])))[:max(cap, sum(1 for c in out if c[0] in ('leaf', 'piece')))]")
def oracle_q1(mods, db=None):
    """The pre-fix `_coarsen` never dropped piece/leaf cells (901 cells -> 451). The cap is a HARD 400 (the database's), the leaf bracket (where the maximum was located) survives, a tree already
    within the cap is returned whole and unflagged."""
    s = mods["window_solver"]
    cells, t = [], 0.0
    for _ in range(450):
        cells.append(["piece", t, t + 100 - Q, 0.5]); t += 100
        cells.append(["dead", t, t + 100 - Q, 0.4]); t += 100
    cells.append(["leaf", t, t + 100 - Q, 0.9])
    assert len(cells) == 901
    out, truncated = s._coarsen(cells, s.MAX_CERT_CELLS)
    assert len(out) <= 400 and truncated is True, (len(out), truncated)
    assert any(c[0] == "leaf" for c in out)
    assert out == sorted(out, key=lambda c: (c[1], c[2]))
    small, flag = s._coarsen(cells[:300], s.MAX_CERT_CELLS)
    assert len(small) == 300 and flag is False
    all_piece = [["piece", 10.0 * k, 10.0 * k + 5.0, 0.5] for k in range(700)]
    out2, flag2 = s._coarsen(all_piece, s.MAX_CERT_CELLS)
    assert len(out2) == 400 and flag2 is True


SHAPES = (("4000 pieces", dict(n_pieces=4000, n_cells=1), None),
          ("6000 pieces", dict(n_pieces=6000, n_cells=1, n_mixed=800), None),
          ("real P3 shape: 650 cells / 3,300 pieces / 600 slivers", dict(n_pieces=3300, n_cells=650, n_slivers=600, n_mixed=300), None),
          ("real worst shape: 1,150 cells / ~520 KB", dict(n_pieces=8000, n_cells=1150, n_slivers=1300, n_mixed=900), 500_000))


@claim("Q-2", "window_solver", "        if size <= max_bytes:\n            return cert", "        if True:\n            return cert", db=True)
def oracle_q2(mods, db):
    """The certificate the writer stores is accepted by the database's own rule — measured in the REAL database (`octet_length(c::text)`, `ka_gochara_solver_certificate_ok`), never
    estimated — for ~4,000 and ~6,000 elementary pieces and for the two real shapes the century produced; at most 400 cells; the digest is over the FULL geometry (so partial geometry is detectable)."""
    for label, shape, min_unbounded in SHAPES:
        tree = make_tree(**shape)
        unbounded = len(json.dumps({"cuts": tree["cuts"], "pieces": tree["pieces"]}))
        assert min_unbounded is None or unbounded > min_unbounded, (label, unbounded)
        cert = build(mods, tree)
        nbytes, ok = db_figures(db, cert)
        assert ok is True and nbytes <= CAP_BYTES, (label, nbytes, ok)
        assert len(cert["cells"]) <= 400, label
        assert cert["geometry_digest"] == full_digest(tree), label


@claim("Q-3", "window_solver", 'return len(format(Decimal(repr(value)), "f"))', "return len(repr(value))", db=True)
def oracle_q3(mods, db):
    """The ruling measures 'on the serialized jsonb exactly as the DB checks it': jsonb prints numbers as plain decimals (`1e-06` -> `0.000001`, `5e-324` -> 326 characters) and a space after `:` and
    `,`, so a `json.dumps` length is not the database's. The builder's figure (and the store mirror's, independently coded) equals `octet_length(c::text)` on certificates built from awkward numbers."""
    s = mods["window_solver"]
    tree = make_tree(40, 30)
    tree["cells"] = [["piece", k * 10.0, k * 10.0 + 5.0, 10.0 ** -(k % 30) / 3.0] for k in range(30)] + [["leaf", 1e-300, 5e-324, 1.5e+22]]
    tree["value"], tree["instant"], tree["upper_bound"] = 1e-12, 123456789.123456789, 0.1 + 0.2
    cert = build(mods, tree)
    nbytes, _ok = db_figures(db, cert)
    assert s.jsonb_text_octets(cert) == nbytes, (s.jsonb_text_octets(cert), nbytes)
    assert wst.jsonb_octets(cert) == nbytes
    assert len(json.dumps(cert)) != nbytes                       # the figure a json.dumps measure would have used is NOT the database's
    for v in ("é€x\"\\\n\t\x01", "plain", ""):
        assert s.jsonb_text_octets({"k": [v, 1, 2.5, None, True, False, {}], "e": []}) == db.execute(
            "SELECT octet_length(%s::jsonb::text)", (json.dumps({"k": [v, 1, 2.5, None, True, False, {}], "e": []}),)).fetchone()[0]


@claim("Q-4", "window_solver", '        attempts.append(({"cuts": [], "pieces": pieces, **omitted(len(cuts), 0)}, True))',
       '        attempts.append(({"cuts": [], "pieces": pieces, **omitted(len(cuts), 0)}, False))')
def oracle_q4(mods, db=None):
    """Never a silent truncation: a bounded certificate says so (`truncated` is the ruling's `certificate_complete=false`, the stored key list being closed) and states the omitted counts inside
    `geometry` (the one stored object 1402 admits extra members in); a certificate that needed no bounding carries neither."""
    complete = build(mods, make_tree(300, 5))
    assert complete["truncated"] is False and "omitted" not in complete["geometry"]
    tree = make_tree(4000, 1)
    cert = build(mods, tree)
    assert cert["truncated"] is True
    om = cert["geometry"]["omitted"]
    assert om["cuts"] == len(tree["cuts"]) - len(cert["geometry"]["cuts"]) and om["pieces"] == len(tree["pieces"]) - len(cert["geometry"]["pieces"]) and om["cells"] == 0
    cells_only = build(mods, make_tree(50, 900))
    assert cells_only["truncated"] is True and len(cells_only["cells"]) == 400 and cells_only["geometry"]["omitted"]["cells"] == 500 and cells_only["geometry"]["omitted"]["pieces"] == 0


@claim("Q-5", "window_solver", 'essential = [p for p in pieces if p[2] in ("mixed", "sliver")]', 'essential = [p for p in pieces if p[2] in ("mixed",)]')
def oracle_q5(mods, db=None):
    """When the geometry is bounded it keeps EVERY mixed piece (g6_plan ranks windows by their count of mixed pieces in the stored geometry) and EVERY sliver piece (the verifier accepts the
    builder's `sliver_pieces_excluded` only when it equals the sliver pieces the stored geometry lists)."""
    tree = make_tree(3000, 1, n_slivers=50, n_mixed=60)
    kept_kinds = lambda geom: [p[2] for p in geom["pieces"]]                                   # noqa: E731
    cert = build(mods, tree, max_bytes=100_000)
    assert cert["truncated"] is True and cert["geometry"]["cuts"] == []
    assert kept_kinds(cert["geometry"]).count("sliver") == 50 and kept_kinds(cert["geometry"]).count("mixed") == 60
    assert len(cert["geometry"]["pieces"]) == 110


@claim("Q-6", "window_solver", '    raise CertificateUnfit(f"the certificate needs', '    return cert\n    raise CertificateUnfit(f"the certificate needs')
def oracle_q6(mods, db=None):
    """A window whose certificate cannot fit even in bounded form is not given an oversize one: `CertificateUnfit`, with counts only in its detail."""
    s = mods["window_solver"]
    with pytest.raises(s.CertificateUnfit) as info:
        build(mods, make_tree(3000, 1, n_slivers=2000), max_bytes=20_000)         # the mandatory (sliver) pieces alone exceed the budget
    assert "20000" in info.value.detail
    assert build(mods, make_tree(3000, 1, n_slivers=2000))["schema"] == s.CERT_SCHEMA      # the real budget still fits the same tree


def _unfit_world(monkeypatch):
    real = sol.stored_certificate
    monkeypatch.setattr(sol, "stored_certificate", functools.partial(real, max_bytes=100))        # a budget nothing fits in: the unfit signal, end to end


@claim("Q-7", "window_sweep", "            except _solver.CertificateUnfit as exc:", "            except ZeroDivisionError as exc:")
def oracle_q7(mods, db=None, monkeypatch=None):
    """The sweep stores the honest null under the solver's own named reason when no certificate fits: no peak, no objective value, no score, no certificate, valence unqualified,
    `unresolved[reason] = 1` (the writer's per-class summary counts it from there)."""
    _unfit_world(monkeypatch)
    w = mods["window_sweep"]
    try:
        (draft,) = w.draft_windows("marriage", _p4_records(), lambda p, v: _rows(p, v), solver=w.PRODUCTION_SOLVER)[0]
    except sol.CertificateUnfit as exc:                      # the specific failure of this claim: the sweep must catch it, not let it abort the class
        pytest.fail(f"the sweep let CertificateUnfit escape instead of storing the honest null: {exc}")
    assert draft.unqualified_reason == sol.REASON_CERTIFICATE == "solver_certificate_incomplete"
    assert draft.peak_instant is None and draft.objective_value is None and draft.score is None and draft.solver_certificate is None
    assert draft.outcome_valence_for_native == "unqualified" and draft.unresolved == {sol.REASON_CERTIFICATE: 1}


def _rows(p, v):
    from .test_a53_window_sweep import _rows_declared
    return _rows_declared(p, v, orb=1.0)


@claim("Q-9", "window_store", "        if len(cells) > CERT_MAX_CELLS:", "        if len(cells) > 10 ** 9:", db=True)
def oracle_q9(mods, db):
    """The pre-insert mirror accepts and refuses exactly what the database's own rule does, on a case set that exercises each limb: the cell cap, the open cap, the byte cap (including a
    certificate small in `json.dumps` and large as jsonb), the closed key lists, types and the solved/blank pairing."""
    st = mods["window_store"]
    base = build(mods, make_tree(30, 5))

    def variant(**kv):
        c = copy.deepcopy(base)
        for k, v in kv.items():
            c[k] = v
        return c
    huge = copy.deepcopy(base)
    huge["geometry"]["pieces"] = [[1e-300 * (k + 1), 5e-324, "up"] for k in range(1000)]          # ~8 KB as json.dumps, > 300 KB as jsonb
    cases = {
        "valid": wrap(base), "no certificate": {k: v for k, v in wrap(base).items() if k != "solver_certificate"},
        "401 cells": wrap(variant(cells=[["piece", float(k), k + 0.5, 0.5] for k in range(401)])),
        "400 cells": wrap(variant(cells=[["piece", float(k), k + 0.5, 0.5] for k in range(400)])),
        "201 open": wrap(variant(open=[[float(k), k + 0.5] for k in range(201)])),
        "bytes via jsonb expansion": wrap(huge),
        "extra certificate key": wrap(variant(extra=1)),
        "extra top key": {**wrap(base), "nope": 1},
        "solved with a reason": wrap(variant(reason="x")),
        "blank without a reason": wrap(variant(outcome="blank")),
        "bad cell kind": wrap(variant(cells=[["bogus", 0.0, 1.0, 0.5]])),
        "digest not hex": wrap(variant(geometry_digest="G" * 64)),
        "truncated not boolean": wrap(variant(truncated="yes")),
        "null certificate": wrap(None),
        "bad policy": {**wrap(base), "policy": "x"},
    }
    for name, q in cases.items():
        ok = db.execute("SELECT public.ka_gochara_window_qualification_ok(%s::jsonb)", (json.dumps(q),)).fetchone()[0]
        assert (st.qualification_shape_defects(q) == []) == ok, (name, ok, st.qualification_shape_defects(q))
    assert not all(not st.qualification_shape_defects(q) for q in cases.values())


# the database claims that need a built grain (Q-8, Q-10) and the verifier claims are below; they follow the same registry


@claim("V-1", "window_cert_check", "    if certificate_incomplete(certificate):", "    if False:")
def oracle_v1(mods, db=None):
    """A certificate flagged `truncated` is never counted as checked: the verifier re-solves the window from scratch (`resolved`, no certificate used) and the stored number survives only
    because that re-solve verified it (AGREED). A complete certificate is still used."""
    c = mods["window_cert_check"]
    h = Hump()
    res, cert = h.solve()
    assert c.certificate_incomplete(cert) is False
    ok = h.check(c, cert, res)
    assert ok.agreed and ok.used_certificate and not ok.resolved and not ok.certificate_incomplete
    flagged = copy.deepcopy(cert)
    flagged["truncated"] = True
    rep = h.check(c, flagged, res)
    assert rep.agreed and rep.resolved and rep.certificate_incomplete and not rep.used_certificate and not rep.fell_back
    wrong = chk.StoredWindow(h.stored(res).peak_instant, res.value + 1.0)                       # a number the re-solve cannot verify is refuted
    refuted = c.check_numbered(lo=h.records()[0].supports[0][0], hi=h.records()[0].supports[0][1], records=h.records(), objective=chk.OBJ_SUM, stored=wrong,
                               position_at=h.pos, certificate={**flagged, "value": res.value + 1.0})
    assert refuted.classification == c.DISAGREEMENT and refuted.certificate_incomplete


@claim("V-5", "window_cert_check",
       "        eng, rep = run(None)\n        return _from_inner(rep, used_certificate=False, fell_back=False, resolved=True, evals=eng.evals, certificate_incomplete=True)",
       "        eng, rep = run(cells)\n        return _from_inner(rep, used_certificate=False, fell_back=False, resolved=True, evals=eng.evals, certificate_incomplete=True)")
def oracle_v5(mods, db=None, monkeypatch=None):
    """SR-KGEW-QUAL-BOUND-AMEND-3 (R-7, B-3): the truncated certificate is the builder's partial evidence; the re-solve is the verifier's INDEPENDENT search, so it starts from nothing —
    `run(None)`, never seeded by the stored cells. Two detectors, each of which reads false on `run(cells)`:
    (1) the engine the incomplete branch builds is handed no cells (a spy on the engine constructor), while a complete certificate's check IS handed its cells;
    (2) behaviourally, a flagged certificate carrying DELIBERATELY WRONG cells (valid in form, a bogus partition) is re-solved with exactly the work of a from-scratch `resolve=True` run on the
        same window; a seeded run would inherit the bogus partition (measured: 758 seeds, 21,832 evaluations against 19,894)."""
    c = mods["window_cert_check"]
    h = Hump()
    res, cert = h.solve()
    seen: list = []

    class Spy(c._SeededEngine):
        def __init__(self, *a, cells=None, **kw):
            seen.append(cells)
            super().__init__(*a, cells=cells, **kw)

    monkeypatch.setattr(c, "_SeededEngine", Spy)
    h.check(c, cert, res)
    assert len(seen) == 1 and seen[0], "a complete certificate's cells seed the check"
    seen.clear()
    bogus = copy.deepcopy(cert)
    bogus["truncated"] = True
    bogus["cells"] = [["piece", 1000.0 * i, 1000.0 * i + 500.0, 1.0e9] for i in range(1, 190)]
    rep = h.check(c, bogus, res)
    assert seen == [None], f"the incomplete branch must start the engine from scratch, not from the stored cells: {[None if s is None else len(s) for s in seen]}"
    scratch = h.check(c, cert, res, resolve=True)
    assert rep.resolved and rep.certificate_incomplete and not rep.used_certificate and rep.agreed
    assert rep.evals == scratch.evals and rep.inner.status == scratch.inner.status, (rep.evals, scratch.evals)


@claim("V-2", "window_cert_check", "    return hashlib.sha256(blob.encode(\"utf-8\")).hexdigest() != cert.get(\"geometry_digest\")",
       "    return False")
def oracle_v2(mods, db=None):
    """`geometry_digest` is over the FULL geometry: a stored geometry that no longer hashes to it is partial whatever the builder's flag says (a detector behind the flag, §N.8). A certificate
    whose geometry matches its digest is complete."""
    c = mods["window_cert_check"]
    _res, cert = Hump().solve()
    assert c.certificate_incomplete(cert) is False
    partial = copy.deepcopy(cert)
    partial["geometry"]["pieces"] = partial["geometry"]["pieces"][:-1]
    assert partial["truncated"] is False and c.certificate_incomplete(partial) is True
    assert c.certificate_incomplete({**cert, "geometry": None}) is True


@claim("V-3", "window_cert_check", "resolved=True, evals=eng.evals, certificate_incomplete=True)", "resolved=True, evals=eng.evals)")
def oracle_v3(mods, db=None):
    """R-6: the verifier's own budget running out on an incomplete certificate is INCONCLUSIVE (`verifier_budget_exhausted`, demoted at seal under the 0.5 % cap), never a pass and never a
    refusal; the report says the certificate was incomplete."""
    c = mods["window_cert_check"]
    h = Hump()
    res, cert = h.solve()
    flagged = copy.deepcopy(cert)
    flagged["truncated"] = True
    rep = h.check(c, flagged, res, max_evals=50)
    assert rep.classification == c.INCONCLUSIVE and "verifier_budget_exhausted" in rep.codes() and rep.certificate_incomplete and not rep.used_certificate


@claim("V-4", "window_verifier", '== _cc.INCOMPLETE_REASON:', '== "never":')
def oracle_v4(mods, db=None):
    """A stored blank under `solver_certificate_incomplete` (the builder's honest null: no certificate could be stored) is INCONCLUSIVE at the verifier under that same named reason — counted,
    never a pass, never a DISAGREEMENT (a blank with no certificate was a `certificate_schema_invalid` disagreement under the budget-blank check)."""
    v = mods["window_verifier"]
    lo = datetime(2030, 1, 1, tzinfo=timezone.utc)
    window = {"peak": None, "lo": lo, "hi": lo, "event_class": "marriage",
              "qualification": {"unqualified_reason": sol.REASON_CERTIFICATE, "unresolved": {sol.REASON_CERTIFICATE: 1}}}
    rep = v._certificate_verdict(window, records=[], objective=chk.OBJ_SUM, position_at=None, against_evaluated=False, ov=None)
    assert rep.classification == cc.INCONCLUSIVE and rep.codes() == ["solver_certificate_incomplete"] and rep.certificate_incomplete
    assert "solver_certificate_incomplete" in cc.INCONCLUSIVE_REASONS


# ── the harness (the R67 pattern) ────────────────────────────────────────────────────────────────────────────────────────────────────────────

_PATHS = {"window_solver": sol, "window_cert_check": cc, "window_store": wst, "window_sweep": ws, "window_verifier": wv}
_COUNT = [0]


def _load(name: str, source: str):
    _COUNT[0] += 1
    mod = types.ModuleType(f"_qb_{name}_{_COUNT[0]}")
    mod.__file__ = _PATHS[name].__file__
    mod.__package__ = PKG
    sys.modules[mod.__name__] = mod
    try:
        exec(compile(source, mod.__file__, "exec"), mod.__dict__)
    finally:
        sys.modules.pop(mod.__name__, None)
    return mod


def real_modules():
    return dict(_PATHS)


def reverted_modules(module: str, old: str, new: str):
    src = Path(_PATHS[module].__file__).read_text()
    assert old != new and src.count(old) == 1, f"the planted reversion must match exactly once, matched {src.count(old)}x: {old[:80]!r}"
    mods = real_modules()
    mods[module] = _load(module, src.replace(old, new))
    return mods


def _disposable(tag: str):
    """A throwaway database: the repo's own AM-5 world (the real migration chain + 1206 + 1240, L1 tables stubbed — `create_am5_database`) with migration 1402 applied verbatim on top.
    Yields the connection; the database is dropped afterwards (never one this fixture did not create)."""
    import psycopg
    admin, name, dsn = create_am5_database(tag)             # KALA_REQUIRE_DB / GOCHARA_A53_REQUIRE_DB=1: an unreachable server FAILS, never skips
    conn = None
    try:
        conn = psycopg.connect(dsn, autocommit=True, connect_timeout=3)
        conn.execute(M1402.read_text())
        yield conn
    finally:
        if conn is not None:
            conn.close()
        drop_am5_database(admin, name)


@pytest.fixture(scope="module")
def mdb():
    """ONE disposable database for the measurement claims (they only call the database's pure functions)."""
    yield from _disposable("qbm")


@pytest.fixture()
def gdb():
    """A fresh disposable database per grain test, with one admitted P3 record materialised (a real window can be written)."""
    from services.gochara_kernel import record_store as rs
    from services.gochara_kernel.rule_registry import RuleRegistryStore
    for conn in _disposable("qbg"):
        RuleRegistryStore(conn).seed()
        with conn.transaction():
            conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
            sky_cid = _sky_convention_id(conn)
            _seed_saturn_crossings(conn, sky_cid)
        store = rs.RecordStore(conn)
        kala_cid = store.ensure_kala_convention()
        _qualification_manifest(conn, store, sky_cid, kala_cid)
        with conn.transaction():
            conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
            rs.write_class_coverage(store, **_coverage_kwargs(store, kala_cid, sky_cid))
        with conn.transaction():
            conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
            rs.materialise_record_grain(store, **{**_grain_kwargs(store, sky_cid), "chart": CHART})
        yield conn


def _run(oracle, mods, db, monkeypatch):
    kw = {}
    import inspect
    if "monkeypatch" in inspect.signature(oracle).parameters:
        kw["monkeypatch"] = monkeypatch
    oracle(mods, db, **kw)


@pytest.mark.parametrize("cid", sorted(CLAIMS))
def test_oracle_passes_on_the_real_code(cid, mdb, monkeypatch):
    _run(CLAIMS[cid][0], real_modules(), mdb, monkeypatch)


@pytest.mark.parametrize("cid", sorted(CLAIMS))
def test_the_single_planted_reversion_fails_the_oracle(cid, mdb, monkeypatch):
    oracle, module, old, new, _db = CLAIMS[cid]
    mods = reverted_modules(module, old, new)         # built OUTSIDE the raises-block: a reversion that no longer matches is an ERROR, not a pass
    with pytest.raises((AssertionError, pytest.fail.Exception)) as info:        # the oracle's own assertion/fail: an unrelated Exception (a TypeError, a broken module) is NOT "caught"
        _run(oracle, mods, mdb, monkeypatch)


def test_every_claim_has_exactly_one_reversion_and_one_oracle():
    assert set(CLAIMS) == {"Q-1", "Q-2", "Q-3", "Q-4", "Q-5", "Q-6", "Q-7", "Q-9", "V-1", "V-2", "V-3", "V-4", "V-5"}
    assert len({(m, old) for _, m, old, _n, _d in CLAIMS.values()}) == len(CLAIMS)


def test_the_mirror_restates_the_databases_caps():
    """The store mirror's caps are the migration's own numbers (read from the function text, not remembered)."""
    src = M1402.read_text()
    assert f"jsonb_array_length(c -> 'cells') <= {wst.CERT_MAX_CELLS}" in src and f"jsonb_array_length(c -> 'open') <= {wst.CERT_MAX_OPEN}" in src
    assert f"octet_length(c::text) <= {wst.CERT_MAX_OCTETS}" in src
    assert (sol.MAX_CERT_CELLS, sol.MAX_OPEN_CELLS, sol.CERT_MAX_BYTES) == (wst.CERT_MAX_CELLS, wst.CERT_MAX_OPEN, wst.CERT_MAX_OCTETS)
    assert 0 < sol.CERT_BYTE_MARGIN and sol.CERT_BYTE_BUDGET == sol.CERT_MAX_BYTES - sol.CERT_BYTE_MARGIN


def test_a_complete_certificate_survives_the_jsonb_round_trip_complete(mdb):
    """The digest detector (V-2) must not fire on a certificate the database stored and returned: a real solved certificate, written through jsonb and read back, is still complete (so
    complete windows keep their cheap certificate check) — and it is not marked incomplete by float formatting."""
    _res, cert = Hump().solve()
    back = mdb.execute("SELECT %s::jsonb", (json.dumps(cert),)).fetchone()[0]
    assert cc.certificate_incomplete(back) is False
    cert2 = sol.stored_certificate(_Result(make_tree(900, 5)), objective=sol.OBJECTIVE_SUM, t0_iso="2030-01-01T00:00:00+00:00")
    assert cert2["truncated"] is False
    assert cc.certificate_incomplete(mdb.execute("SELECT %s::jsonb", (json.dumps(cert2),)).fetchone()[0]) is False


# ── the end-to-end database claims (a built grain): Q-8 (the stored blank passes the full constraint) and Q-10 (a pre-insert hit names the window) ──────────

def _blank_draft(draft):
    """The draft the sweep builds for an unfit certificate (Q-7 proves the sweep's output; here it is stored)."""
    import dataclasses
    return dataclasses.replace(draft, peak_instant=None, score=None, evidence_for=None, evidence_against=None, objective_value=None,
                               outcome_valence_for_native="unqualified", severity=None, unqualified_reason=sol.REASON_CERTIFICATE,
                               unresolved={sol.REASON_CERTIFICATE: 1}, solver_certificate=None, null_states_used=["unqualified"])


def _grain_draft(conn):
    from services.gochara_kernel import record_store  # noqa: F401
    store = wst.WindowStore(conn)
    recs = store.read_grain(chart_id=CHART_ID, generation=GEN, event_class="marriage", path_id="P3", rule_version="1.0.0", position_at=_p3_probe)
    (draft,), _ = ws.draft_windows("marriage", recs, ws.registry_factor_rows)
    return store, draft


def _write(store, conn, drafts):
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        return store.replace_grain_windows(chart_id=CHART_ID, generation=GEN, event_class="marriage", path_id="P3", rule_version="1.0.0", drafts=drafts)


def test_q8_the_unfit_blank_is_stored_and_passes_the_full_shape_check(gdb):
    store, draft = _grain_draft(gdb)
    blank = _blank_draft(draft)
    counts = _write(store, gdb, [blank])                                   # the INSERT is checked by kgew_qualification_shape_ck and kgew_unqualified_no_result_ck
    assert counts["windows"] == 1
    row = gdb.execute("SELECT peak_instant, objective_value, score, qualification ->> 'unqualified_reason', qualification -> 'solver_certificate',"
                      " public.ka_gochara_window_qualification_ok(qualification) FROM public.ka_gochara_eval_window").fetchone()
    assert row[0] is None and row[1] is None and row[2] is None and row[3] == "solver_certificate_incomplete" and row[4] is None and row[5] is True
    q = gdb.execute("SELECT qualification FROM public.ka_gochara_eval_window").fetchone()[0]
    assert wst.qualification_shape_defects(q) == []                        # the mirror agrees on the stored record


def test_q8_reverted_a_blank_under_a_reason_with_a_number_is_refused_by_the_database(gdb):
    """The detector can read false: the same row with a number left on it IS refused by the database (so the passing row above is not vacuous)."""
    import dataclasses
    import psycopg
    store, draft = _grain_draft(gdb)
    with pytest.raises(psycopg.errors.CheckViolation):
        _write(store, gdb, [dataclasses.replace(_blank_draft(draft), peak_instant=draft.peak_instant or PG_T0, objective_value=0.5)])


def _q10_oracle(mods, conn):
    """Ruling 5/6: a pre-insert hit (a certificate over 400 cells; one over 256 KiB as the database measures it) is a loud DEFECT naming the window key and the constraint, raised BEFORE any
    row goes out; the same draft with a fitting certificate is stored."""
    import dataclasses
    st = mods["window_store"]
    store, draft = _grain_draft(conn)
    store = st.WindowStore(conn)
    wid = str(st.window_uuid(chart_id=CHART_ID, generation=GEN, event_class="marriage", path_id="P3", rule_version="1.0.0", interval=draft.interval))
    good = build(mods, make_tree(30, 5))
    too_many = copy.deepcopy(good)
    too_many["cells"] = [["piece", float(k), k + 0.5, 0.5] for k in range(401)]
    too_big = copy.deepcopy(good)
    too_big["geometry"]["pieces"] = [[float(k) * 3600.123456789, float(k) * 3600.123456789 + 1.5, "up"] for k in range(6000)]
    assert db_figures(conn, too_big)[0] > CAP_BYTES
    for label, cert in (("401 cells", too_many), ("over 256 KiB", too_big)):
        with pytest.raises(st.QualificationShapeDefect) as info:
            _write(store, conn, [dataclasses.replace(draft, solver_certificate=cert)])
        assert wid in str(info.value) and info.value.window_key == wid and "kgew_qualification_shape_ck" in str(info.value), label
        assert conn.execute("SELECT count(*) FROM public.ka_gochara_eval_window").fetchone()[0] == 0, label
    _write(store, conn, [dataclasses.replace(draft, solver_certificate=good)])           # the same draft with a fitting certificate is stored
    assert conn.execute("SELECT count(*) FROM public.ka_gochara_eval_window").fetchone()[0] == 1


def test_q10_a_pre_insert_hit_names_the_window_key_before_any_row_goes_out(gdb):
    _q10_oracle(real_modules(), gdb)


def test_q10_the_single_planted_reversion_fails_the_oracle(gdb):
    """Planted reversion of Q-10: the mirror's verdict is ignored (`if problems:` -> `if False:`), so the INSERT reaches the database, which refuses by CONSTRAINT name and never names the window."""
    mods = reverted_modules("window_store", "                if problems:\n                    raise QualificationShapeDefect(", "                if False:\n                    raise QualificationShapeDefect(")
    with pytest.raises(Exception):
        _q10_oracle(mods, gdb)
