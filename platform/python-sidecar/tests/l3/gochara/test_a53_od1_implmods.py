"""SR-OD1 R9c-A10-1 (G-8 / EQUIVALENCE_RECORD): the window solver and its independent checker are part of the governed implementation identity.

Claims: (1) every module the SR-OD1 lanes added sits in exactly one stage, never geometry; (2) editing `window_solver` or `window_solver_check` moves the manifest's WINDOW implementation digest — and nothing else (the geometry
pin, the qualified GEOM-PIN-ONCE value (with its recorded amend-5), must not move; evaluation is untouched by an edit to a window-stage module).

Why it needs its own oracle: neither module is imported by the writer yet (the sweep calls the solver from S3), so the import-closure coverage test
(`test_a53_input_vector`, AM-16) cannot see it; only the list itself puts it in the code fingerprint. The checker is deliberately independent of the
solver (it shares no import with it), so it is listed on its own.

Planted reversion (the ONE for this claim): remove either name from `input_vector.IMPLEMENTATION_MODULES["window"]` -> every test below fails.
Detector: the real digest functions (`input_vector.implementation_digests`, `input_vector_verifier.module_digests`) over the real module files; the edit is
made to a COPY of the real source, never to the repository file.
"""
from __future__ import annotations

import importlib
import importlib.util
import types
from pathlib import Path

import pytest

from services.gochara_kernel import input_vector as iv
from services.gochara_kernel import input_vector_verifier as ivv

SOLVER = "services.gochara_kernel.window_solver"
CHECKER = "services.gochara_kernel.window_solver_check"


#: Every module the SR-OD1 lanes added to the build/verification path and the ONE stage it governs (never geometry). The solver and checker are the
#: R9c-A10-1 finding; the rest were audited with it (all kernel/rules modules added on od1-integration vs main) and pinned so a later removal fails here.
LANE_MODULES = {
    "services.gochara_kernel.window_solver": "window", "services.gochara_kernel.window_solver_check": "window",
    "services.gochara_kernel.numerical_window_gate": "window", "services.gochara_kernel.p1_operands_check": "window",
    "services.gochara_kernel.vedha_verifier": "window", "services.gochara_kernel.vedha_source": "window",
    "services.gochara_kernel.p1_operands": "evaluation", "services.gochara_kernel.p1_nature_operands": "evaluation",
    "services.gochara_rules.p1_valence": "evaluation",
}


@pytest.mark.parametrize("name,stage", sorted(LANE_MODULES.items()))
def test_every_od1_lane_module_sits_in_exactly_its_stage(name, stage):
    assert [st for st, mods in iv.IMPLEMENTATION_MODULES.items() if name in mods] == [stage], name


def _edited_copy(name: str, tmp_path: Path, *, edit: bool) -> Path:
    src = Path(importlib.import_module(name).__file__).read_text(encoding="utf-8")
    out = tmp_path / (name.rsplit(".", 1)[1] + ("_edited.py" if edit else "_same.py"))
    out.write_text(src + ("\n_EDITED = 1\n" if edit else ""), encoding="utf-8")
    return out


def _via_import_module(monkeypatch, name: str, path: Path):
    real = importlib.import_module
    monkeypatch.setattr(iv.importlib, "import_module",
                        lambda n, *a, **k: types.SimpleNamespace(__file__=str(path)) if n == name else real(n, *a, **k))
    return iv.implementation_digests


def _via_find_spec(monkeypatch, name: str, path: Path):
    real = importlib.util.find_spec
    monkeypatch.setattr(importlib.util, "find_spec",
                        lambda n, *a, **k: types.SimpleNamespace(origin=str(path)) if n == name else real(n, *a, **k))
    return lambda mods: ivv.module_digests(mods)


@pytest.mark.parametrize("name", [SOLVER, CHECKER])
@pytest.mark.parametrize("via", [_via_import_module, _via_find_spec], ids=["manifest_builder", "verifier"])
def test_editing_the_module_moves_the_window_digest_and_only_that(name, via, tmp_path, monkeypatch):
    mods = iv.IMPLEMENTATION_MODULES
    before = ivv.module_digests(mods)
    same = via(monkeypatch, name, _edited_copy(name, tmp_path, edit=False))(mods)
    assert same == before, "control: an unedited copy of the same bytes changes nothing"
    monkeypatch.undo()
    after = via(monkeypatch, name, _edited_copy(name, tmp_path, edit=True))(mods)
    assert after["window"] != before["window"], f"editing {name} must change the window implementation digest"
    assert after["geometry"] == before["geometry"] and after["evaluation"] == before["evaluation"]
