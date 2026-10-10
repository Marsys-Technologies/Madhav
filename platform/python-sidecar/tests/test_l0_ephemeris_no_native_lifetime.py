"""
test_l0_ephemeris_no_native_lifetime.py -- SS N-384 (PR-S6), item 4.

`get_ephemeris_cache_native_lifetime()` was dead code (no caller anywhere) that built a payload
with one person's name, birth date, birth time and birthplace. It is deleted; this test keeps it
(and a payload of that shape) from coming back. Static (AST) so it needs no psycopg or database.
"""
from __future__ import annotations

import ast
from pathlib import Path

PATH = Path(__file__).resolve().parent.parent / "brahmagyan" / "l0_ephemeris.py"


def _tree() -> ast.Module:
    return ast.parse(PATH.read_text())


def test_native_lifetime_function_is_gone() -> None:
    names = {n.name for n in ast.walk(_tree()) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    assert "get_ephemeris_cache_native_lifetime" not in names
    # the neighbouring legitimate resource is still there, so the scan is not vacuous
    assert "get_ephemeris_cache_year" in names


def test_no_native_identity_payload_in_the_module() -> None:
    tree = _tree()
    strings = [n.value.lower() for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    assert not [s for s in strings if "abhisek" in s or "mohanty" in s]
    assert not [s for s in strings if "native-lifetime" in s]
    # no dict literal carrying a "birth_time_ist" key
    keys = [k.value for d in ast.walk(tree) if isinstance(d, ast.Dict) for k in d.keys
            if isinstance(k, ast.Constant) and isinstance(k.value, str)]
    assert "birth_time_ist" not in keys and "birth_location" not in keys
