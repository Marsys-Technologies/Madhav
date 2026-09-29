"""Suvarṇa census runner (B6, review pass 3) — the one command the swarm's own permission
allowlist ever needs to grant for the Nikaṣa asset census.

    python -m suvarna_tracker.census_run --layer LAYER --out PATH [--wait SECONDS] [--emit]
        [--actor NAME] [--home DIR]

Review pass 3 found that the template's wildcard `Bash(python3 -m suvarna_tracker.census_lock
--wait * --emit --actor * -- bash -c '... asset_census.py *)` allow could not actually be expressed
as a single Claude Code permission rule (rules are a single fixed prefix plus one trailing `*`, per
`runtime/settings.template.json`'s own `_meta` finding — not a multi-wildcard glob), and that even
if it could, `census_lock --emit -- <any command>` is a wrapper around every other Bash deny in the
template. This module closes both gaps: it builds the one fixed, validated invocation itself from
`--layer`/`--out` (never taking a caller-supplied command), and always runs it through
`census_lock.run_locked(..., census_only=True)` so the command is independently re-validated even
if this module's own construction ever drifted. The permission template allows exactly
``Bash(python3 -m suvarna_tracker.census_run *)`` — one command, not an escape hatch.

CODE-35 (review pass 3 disposition, arch §12.13/§12.15): the census inspector's checkout switches
from the legacy read-only ``/Users/Dev/madhav-nikasha`` to the ``suvarna/trunk`` worktree once E4.1
lands the inspector on ``main``. ``SUVARNA_CENSUS_ROOT``, when set, selects which of those two — and
only those two (`census_root`, mirrored by `census_lock.CENSUS_ALLOWED_ROOTS` as an independent
re-validation) — this module builds its command against; it is never a free-form, caller-supplied
checkout path.
"""
from __future__ import annotations

import argparse
import os
import re
import shlex
import sys

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from suvarna_tracker import census_lock  # noqa: E402

DEFAULT_NIKASHA_ROOT = "/Users/Dev/madhav-nikasha"
TRUNK_ROOT = "/Users/Dev/suvarna/trunk"
# CODE-35: the only two checkouts the census is ever allowed to run from. Kept as the same literal
# pair `census_lock.CENSUS_ALLOWED_ROOTS` independently re-validates against — not derived from one
# shared "source of truth" import, so a change to one without the other is a visible test failure
# rather than a silent widening on both sides at once.
CENSUS_ALLOWED_ROOTS = (DEFAULT_NIKASHA_ROOT, TRUNK_ROOT)
CENSUS_ROOT_ENV = "SUVARNA_CENSUS_ROOT"
DEFAULT_PGENV = "~/.config/suvarna/pgenv.sh"

# A layer name is a plain token (arch's own `ka_*`/`bo_*`/... family or a level number) — never a
# shell metacharacter, never a path.
_LAYER_RE = re.compile(r"^[A-Za-z0-9_-]+$")
# --out must be an absolute path with no shell metacharacters (the same charset shlex.quote itself
# never needs to escape, so the built command's regex in census_lock.py stays exact).
_UNSAFE_OUT_RE = re.compile(r"[^\w.@%+:,/-]")


class CensusRunError(ValueError):
    pass


def census_root() -> str:
    """The checkout the census inspector runs from (CODE-35). `SUVARNA_CENSUS_ROOT`, when set,
    must be exactly one of `CENSUS_ALLOWED_ROOTS` — never an arbitrary path; the switch from the
    legacy checkout to `suvarna/trunk` at E4.1 is a deliberate, named decision, not a free-form
    setting. Raises `CensusRunError` for anything else."""
    root = os.environ.get(CENSUS_ROOT_ENV) or DEFAULT_NIKASHA_ROOT
    if root not in CENSUS_ALLOWED_ROOTS:
        raise CensusRunError(f"{CENSUS_ROOT_ENV} must be one of {CENSUS_ALLOWED_ROOTS}: {root!r}")
    return root


def build_command(layer: str, out: str, nikasha_root: str | None = None,
                  pgenv: str = DEFAULT_PGENV) -> list[str]:
    """The one fixed, validated `bash -c '...'` invocation `census_lock.is_census_only_command`
    accepts. Raises `CensusRunError` for anything that does not validate — never builds a command
    from an unvalidated value. `nikasha_root` defaults to `census_root()` (CODE-35); an explicit
    caller-supplied value is still checked against `CENSUS_ALLOWED_ROOTS`, never trusted bare."""
    root = nikasha_root if nikasha_root is not None else census_root()
    if root not in CENSUS_ALLOWED_ROOTS:
        raise CensusRunError(f"census checkout must be one of {CENSUS_ALLOWED_ROOTS}: {root!r}")
    if not layer or not _LAYER_RE.match(layer):
        raise CensusRunError(f"--layer must match {_LAYER_RE.pattern!r}: {layer!r}")
    if not out or not os.path.isabs(out) or _UNSAFE_OUT_RE.search(out):
        raise CensusRunError(f"--out must be an absolute path with no shell metacharacters: {out!r}")
    inner = (f"source {pgenv} && cd {root} && "
             f"python3 platform/scripts/governance/asset_census.py "
             f"--layer {shlex.quote(layer)} --out {shlex.quote(out)}")
    return ["bash", "-c", inner]


def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Run the Nikaṣa asset census inspector under the census lock")
    ap.add_argument("--layer", required=True, help="the layer to census (a plain token, e.g. ka_gochara)")
    ap.add_argument("--out", required=True, help="absolute output path for the census report")
    ap.add_argument("--wait", type=float, default=0.0, help="seconds to wait for the census lock")
    ap.add_argument("--emit", action="store_true", help="emit a note event on acquire and on release")
    ap.add_argument("--actor", default="census-run", help="actor name used for --emit notes")
    ap.add_argument("--home", default=os.environ.get("SUVARNA_HOME", "/Users/Dev/suvarna"))
    return ap


def main(argv: list[str] | None = None) -> int:
    a = build_arg_parser().parse_args(argv)
    try:
        command = build_command(a.layer, a.out)
    except CensusRunError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    return census_lock.run_locked(a.home, command, wait=a.wait, emit_flag=a.emit, actor=a.actor,
                                  census_only=True)


if __name__ == "__main__":
    raise SystemExit(main())
