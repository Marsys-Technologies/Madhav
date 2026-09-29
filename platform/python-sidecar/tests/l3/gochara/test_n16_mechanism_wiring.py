"""
N-16 — Wiring-truth detector.

A permanent three-way consistency check between:
  1. `services/gochara_v3/engine.py` — which mechanism modules are imported and
     whose modifier variables are actually multiplied into the production
     `raw_lambda` (= lambda_v3);
  2. `services/gochara_v3/mechanism_register.yaml` — the docs-of-record set of
     mechanisms (admitted + structural-only + any legacy modifier currently in
     use);
  3. `scripts/kala_admission.w44_weight_fitting.MECHANISM_ENGINE_WIRED` — the
     machine-checked dict that w44's ablation logic uses.

The test fails whenever any of these three sources disagrees about a mechanism
that is admitted, structural, or wired into the lambda product. It must be green
before any w44 re-fit is trusted.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest


_SIDECAR_ROOT = Path(__file__).resolve().parents[3]
_ENGINE_PY = _SIDECAR_ROOT / "services" / "gochara_v3" / "engine.py"
_REGISTER_YAML = _SIDECAR_ROOT / "services" / "gochara_v3" / "mechanism_register.yaml"
_MECHANISMS_DIR = _SIDECAR_ROOT / "services" / "gochara_v3" / "mechanisms"


def _parse_yaml_list(path: Path) -> list[dict[str, Any]]:
    """Load the mechanism list from the docs-of-record YAML.

    Uses PyYAML if available; falls back to a minimal line parser sufficient
    for the register format.
    """
    text = path.read_text()
    try:
        import yaml

        data = yaml.safe_load(text)
    except ImportError:
        data = _simple_yaml_list_parse(text)
    return data.get("mechanisms", [])


def _simple_yaml_list_parse(text: str) -> dict[str, list[dict[str, Any]]]:
    """Fallback parser for the register YAML when PyYAML is absent.

    The register has a top-level `mechanisms:` key whose value is a list of
    indented entries. Each entry starts with `  - toggle_key:` and the rest of
    its scalar fields are indented four spaces.
    """
    mechanisms: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        stripped = line.lstrip()
        if stripped.startswith("- toggle_key:"):
            if current is not None:
                mechanisms.append(current)
            current = {"toggle_key": stripped.split(":", 1)[1].strip()}
        elif current is not None and line.startswith("    "):
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip().strip('"')
            if key in ("toggle_key", "mechanism_id", "admission_state", "weight_type", "module_path"):
                current[key] = val
    if current is not None:
        mechanisms.append(current)
    return {"mechanisms": mechanisms}


def _load_register_entries() -> list[dict[str, Any]]:
    return _parse_yaml_list(_REGISTER_YAML)


def _module_toggle_key(module_name: str) -> str:
    """Read a mechanism module's TOGGLE_KEY constant if it exists."""
    mod_path = _MECHANISMS_DIR / f"{module_name}.py"
    if not mod_path.exists():
        return module_name
    try:
        tree = ast.parse(mod_path.read_text())
    except SyntaxError:
        return module_name
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "TOGGLE_KEY"
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            return node.value.value
    return module_name


def _derive_engine_wired_set(engine_path: Path = _ENGINE_PY) -> set[str]:
    """Return toggle keys whose modifiers are multiplied into raw_lambda."""
    tree = ast.parse(engine_path.read_text())

    # alias -> module name for imports from services.gochara_v3.mechanisms
    alias_to_module: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "services.gochara_v3.mechanisms":
            for alias in node.names:
                alias_to_module[alias.asname or alias.name] = alias.name

    # Trace mechanism results into the variables that reach raw_lambda.
    # Two patterns:
    #   _result = _alias.compute(...);  modifier_var = _result.modifier
    #   modifier_var = _alias.compute(...).modifier
    alias_to_module: dict[str, str] = {}
    result_var_to_alias: dict[str, str] = {}
    modifier_var_to_alias: dict[str, str] = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "services.gochara_v3.mechanisms":
            for alias in node.names:
                alias_to_module[alias.asname or alias.name] = alias.name

    def _is_alias_compute_call(node: ast.AST) -> str | None:
        """Return the alias name if node is <alias>.compute(...)."""
        if not isinstance(node, ast.Call):
            return None
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "compute":
            return None
        base = func.value
        if isinstance(base, ast.Name) and base.id in alias_to_module:
            return base.id
        return None

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            target_name = node.targets[0].id
            val = node.value

            # Pattern 1: _result = _alias.compute(...)
            alias = _is_alias_compute_call(val)
            if alias is not None:
                result_var_to_alias[target_name] = alias
                continue

            # Pattern 2: modifier_var = <expr>.modifier
            if isinstance(val, ast.Attribute) and val.attr == "modifier":
                inner = val.value
                # 2a: modifier_var = _alias.compute(...).modifier
                alias = _is_alias_compute_call(inner)
                if alias is not None:
                    modifier_var_to_alias[target_name] = alias
                    continue
                # 2b: modifier_var = _result.modifier where _result came from _alias.compute(...)
                if isinstance(inner, ast.Name) and inner.id in result_var_to_alias:
                    modifier_var_to_alias[target_name] = result_var_to_alias[inner.id]

    # names used in the raw_lambda assignment
    raw_lambda_names: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "raw_lambda"
        ):
            for child in ast.walk(node.value):
                if isinstance(child, ast.Name):
                    raw_lambda_names.add(child.id)

    wired_aliases = {
        alias
        for var, alias in modifier_var_to_alias.items()
        if var in raw_lambda_names
    }
    # Also count a mechanism whose result variable is used directly in raw_lambda
    for var, alias in result_var_to_alias.items():
        if var in raw_lambda_names:
            wired_aliases.add(alias)

    wired_modules = {alias_to_module[alias] for alias in wired_aliases}
    return {_module_toggle_key(mod) for mod in wired_modules}


class TestMechanismWiringTruth:
    """N-16 three-way wiring detector."""

    def test_register_entries_have_toggle_keys(self):
        entries = _load_register_entries()
        assert entries, "mechanism_register.yaml should contain mechanisms"
        for e in entries:
            assert "toggle_key" in e and e["toggle_key"], f"register entry missing toggle_key: {e}"

    def test_wired_mechanisms_are_in_register_and_dict(self):
        """Any mechanism multiplied into raw_lambda must be in the register
        and marked wired in MECHANISM_ENGINE_WIRED."""
        from scripts.kala_admission.w44_weight_fitting import MECHANISM_ENGINE_WIRED

        engine_wired = _derive_engine_wired_set()
        register_set = {e["toggle_key"] for e in _load_register_entries()}

        missing_from_register = engine_wired - register_set
        assert not missing_from_register, (
            f"mechanisms wired in engine.py but absent from register: "
            f"{missing_from_register}"
        )

        not_marked_wired = {
            tk for tk in engine_wired
            if not MECHANISM_ENGINE_WIRED.get(tk, True)
        }
        assert not not_marked_wired, (
            f"mechanisms wired in engine.py but MECHANISM_ENGINE_WIRED says False: "
            f"{not_marked_wired}"
        )

    def test_admitted_mechanisms_match_engine_wiring(self):
        """Every admitted mechanism in the register must be present in
        MECHANISM_ENGINE_WIRED, and its value must match whether engine.py
        multiplies it into raw_lambda."""
        from scripts.kala_admission.w44_weight_fitting import MECHANISM_ENGINE_WIRED

        engine_wired = _derive_engine_wired_set()
        errors: list[str] = []
        for entry in _load_register_entries():
            tk = entry.get("toggle_key")
            state = entry.get("admission_state")
            if not tk:
                continue
            if state == "structural_only":
                # Structural-only mechanisms are not expected in the lambda product.
                if MECHANISM_ENGINE_WIRED.get(tk, True) is not False:
                    errors.append(
                        f"{tk} (structural_only) should be marked False in MECHANISM_ENGINE_WIRED"
                    )
                continue
            # Admitted / legacy mechanisms must be explicitly tracked.
            if tk not in MECHANISM_ENGINE_WIRED and tk not in engine_wired:
                errors.append(
                    f"{tk} is in the register but not in MECHANISM_ENGINE_WIRED and not wired"
                )
                continue
            expected = tk in engine_wired
            actual = MECHANISM_ENGINE_WIRED.get(tk, True)
            if expected != actual:
                errors.append(
                    f"{tk}: engine wired={expected}, MECHANISM_ENGINE_WIRED={actual}"
                )

        assert not errors, "wiring disagreements:\n" + "\n".join(errors)

    def test_no_extraneous_true_entries_in_dict(self):
        """MECHANISM_ENGINE_WIRED must not claim True for a mechanism that is
        not wired into the lambda product."""
        from scripts.kala_admission.w44_weight_fitting import MECHANISM_ENGINE_WIRED

        engine_wired = _derive_engine_wired_set()
        register_set = {e["toggle_key"] for e in _load_register_entries()}

        false_positives = {
            tk for tk, wired in MECHANISM_ENGINE_WIRED.items()
            if wired and tk in register_set and tk not in engine_wired
        }
        assert not false_positives, (
            f"MECHANISM_ENGINE_WIRED claims True for unwired mechanisms: {false_positives}"
        )
