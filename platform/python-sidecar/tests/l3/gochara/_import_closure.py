"""The writer's static import closure over services.gochara_kernel + services.gochara_rules (AST, no import
side effects). Used by the AM-16 coverage test: every module whose edit could change a result must sit in
an `implementation` stage list, or editing it would not move the input vector."""
from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

ROOTS = ("services.gochara_kernel", "services.gochara_rules")


def _spec(name: str):
    try:
        return importlib.util.find_spec(name)
    except (ModuleNotFoundError, AttributeError, ValueError):
        return None


def _file(name: str) -> Path | None:
    spec = _spec(name)
    return Path(spec.origin) if spec and spec.origin and str(spec.origin).endswith(".py") else None


def _imports(name: str) -> set[str]:
    f = _file(name)
    if f is None:
        return set()
    pkg = name if f.name == "__init__.py" else name.rsplit(".", 1)[0]
    out: set[str] = set()
    for n in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
        if isinstance(n, ast.Import):
            out.update(a.name for a in n.names)
        elif isinstance(n, ast.ImportFrom):
            if n.level:
                base = pkg.split(".")
                base = base[: len(base) - (n.level - 1)]
                m = ".".join(base + ([n.module] if n.module else []))
            else:
                m = n.module or ""
            out.add(m)
            out.update(f"{m}.{a.name}" for a in n.names)
    return out


def writer_closure(root: str = "pipeline.orchestrator.writers.ka_gochara_v5") -> set[str]:
    seen: set[str] = set()
    stack = [root]
    while stack:
        m = stack.pop()
        if m in seen:
            continue
        seen.add(m)
        for i in _imports(m):
            if (i.startswith(ROOTS) or i == root) and _file(i) is not None and i not in seen:
                stack.append(i)
    return {m for m in seen if m.startswith(ROOTS) and not m.endswith(".__init__")} - {
        "services.gochara_kernel", "services.gochara_rules"}
