"""Generate (and check) the Suvarṇa execution sessions' local permission allowlist (L.15).

    python -m suvarna_tracker.runtime_settings --write <dir>/.claude/settings.local.json
    python -m suvarna_tracker.runtime_settings --write <dir>/.claude/settings.local.json --check
    python -m suvarna_tracker.runtime_settings --write $SUVARNA_HOME/config/claude-settings.json --check

This writes the **local**, uncommitted ``.claude/settings.local.json`` the two unattended execution
sessions read (``claude --permission-mode dontAsk`` in ``/Users/Dev/suvarna/hq``), from the committed
template ``suvarna_tracker/runtime/settings.template.json``. It never writes ``.claude/settings.json``
— that file is committed and would change every session of the repo, not only the two Suvarṇa
sessions (CLAUDE.md file-placement discipline; the L.15 brief's own hard constraint). ``--check``
compares an existing file against the template without writing anything, for drift detection in a
periodic health check.

CODE-20 (C22, arch §2.4): the same template also backs the N-25 settings file,
``$SUVARNA_HOME/config/claude-settings.json`` — the one every launch passes explicitly with
``--settings`` once the separate ``suvarna`` user exists. That exact path (never merely any file
named ``claude-settings.json``) is accepted as a second valid target, alongside ``settings.local.json``
anywhere; the Monitor's ``isolation`` check (CODE-12) is what runs ``--check`` against it.

Design rules:
- **The target path is validated before anything is read or written.** A path is refused outright
  (exit 2) unless it is exactly a ``settings.local.json`` file, or exactly
  ``$SUVARNA_HOME/config/claude-settings.json`` — this is the one guard standing between this tool
  and accidentally touching a committed project settings file (any other ``settings.json``, however
  named or wherever nested, stays refused).
- **Atomic write.** tmp-then-``os.replace`` (same pattern as ``decisions.mirror_to``), so a crash
  mid-write never leaves a half-written settings file behind.
- **The template is the one source of truth.** Nothing here invents a permission rule; every rule in
  ``runtime/settings.template.json`` is documented there (and in
  ``00_ARCHITECTURE/briefs/suvarna/runtime/INTERIM_RUNTIME_v1_0.md``) with what was and was not
  confirmed against the installed CLI (v2.1.239).
"""
from __future__ import annotations

import argparse
import json
import os
import sys

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET_BASENAME = "settings.local.json"
# CODE-20: the N-25 settings file's basename (arch §2.4). Accepted only at the exact
# `claude_settings_target_path()` location, never anywhere a file happens to be named this.
CLAUDE_SETTINGS_BASENAME = "claude-settings.json"


class RuntimeSettingsError(ValueError):
    pass


def default_template_path() -> str:
    return os.path.join(HERE, "runtime", "settings.template.json")


def claude_settings_target_path(home: str | None = None) -> str:
    """The one location `claude-settings.json` is ever accepted at: `$SUVARNA_HOME/config/`. `home`
    defaults to `$SUVARNA_HOME` (or the same `/Users/Dev/suvarna` fallback every other tool in this
    package uses)."""
    home = home or os.environ.get("SUVARNA_HOME", "/Users/Dev/suvarna")
    return os.path.join(home, "config", CLAUDE_SETTINGS_BASENAME)


def load_template(path: str | None = None) -> dict:
    path = path or default_template_path()
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise RuntimeSettingsError(f"{path} does not contain a JSON object")
    return data


def validate_target_path(path: str, home: str | None = None) -> None:
    """Refuse anything that is not exactly a ``settings.local.json`` file, or exactly the N-25
    settings file at ``claude_settings_target_path(home)``. This is the one guard against ever
    generating a committed ``.claude/settings.json`` by a typo or a copy-paste — a project-wide
    committed settings file would affect every session of the repo, not only the Suvarṇa execution
    sessions this tool is for."""
    if os.path.basename(path) == TARGET_BASENAME:
        return
    if os.path.abspath(path) == os.path.abspath(claude_settings_target_path(home)):
        return
    raise RuntimeSettingsError(
        f"refusing to write {path!r}: the target file name must be exactly {TARGET_BASENAME!r}, or "
        f"the path must be exactly {claude_settings_target_path(home)!r} — never a repository's "
        f"'settings.json' (however named or nested), which would affect every session of the repo, "
        f"not only the Suvarṇa execution sessions this tool is for")


def write_settings(target_path: str, template: dict | None = None, home: str | None = None) -> dict:
    """Validate the target path, then atomically write the template (pretty-printed) to it. Returns
    the written object."""
    validate_target_path(target_path, home)
    template = template if template is not None else load_template()
    out_dir = os.path.dirname(os.path.abspath(target_path))
    os.makedirs(out_dir, exist_ok=True)
    tmp = f"{target_path}.tmp.{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(template, f, indent=2, ensure_ascii=False, sort_keys=False)
        f.write("\n")
    os.replace(tmp, target_path)
    return template


def _walk_diff(actual, expected, prefix: str, diffs: list[str]) -> None:
    if isinstance(expected, dict) and isinstance(actual, dict):
        for key in sorted(set(actual) | set(expected)):
            path = f"{prefix}.{key}" if prefix else key
            if key not in actual:
                diffs.append(f"missing: {path}")
            elif key not in expected:
                diffs.append(f"unexpected: {path}")
            else:
                _walk_diff(actual[key], expected[key], path, diffs)
    elif actual != expected:
        diffs.append(f"changed: {prefix} ({actual!r} != template's {expected!r})")


def diff_settings(actual: dict, expected: dict) -> list[str]:
    """Deep, dotted-path differences between an existing settings object and the template. An empty
    list means no drift."""
    diffs: list[str] = []
    _walk_diff(actual, expected, "", diffs)
    return sorted(diffs)


def check_settings(target_path: str, template: dict | None = None) -> list[str]:
    """Compare an existing file at ``target_path`` against the template. Never writes anything.
    Returns the list of differences (empty = no drift); a missing or unparseable file is itself
    reported as one difference, never silently treated as "matches"."""
    template = template if template is not None else load_template()
    try:
        with open(target_path, encoding="utf-8") as f:
            actual = json.load(f)
    except FileNotFoundError:
        return [f"missing: {target_path} does not exist"]
    except ValueError as exc:
        return [f"unreadable: {target_path} is not valid JSON ({exc})"]
    if not isinstance(actual, dict):
        return [f"unreadable: {target_path} does not contain a JSON object"]
    return diff_settings(actual, template)


def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Generate or check the Suvarṇa execution sessions' local settings.local.json")
    ap.add_argument("--write", required=True, metavar="PATH",
                    help="the settings.local.json path to write (or, with --check, to validate)")
    ap.add_argument("--check", action="store_true",
                    help="do not write; instead compare the existing file at PATH against the "
                         "template and exit 1 on any drift")
    ap.add_argument("--template", metavar="PATH", default=None,
                    help="override the template path (default: suvarna_tracker/runtime/settings.template.json)")
    ap.add_argument("--home", metavar="DIR", default=None,
                    help="override $SUVARNA_HOME for validating the claude-settings.json target (CODE-20)")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)

    try:
        validate_target_path(args.write, args.home)
    except RuntimeSettingsError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2

    try:
        template = load_template(args.template)
    except (OSError, ValueError, RuntimeSettingsError) as exc:
        print(f"refused: could not load template: {exc}", file=sys.stderr)
        return 2

    if args.check:
        diffs = check_settings(args.write, template)
        if diffs:
            print(f"drift: {args.write} differs from the template ({len(diffs)} difference(s)):",
                  file=sys.stderr)
            for d in diffs:
                print(f"  - {d}", file=sys.stderr)
            return 1
        print(f"ok: {args.write} matches the template")
        return 0

    write_settings(args.write, template, home=args.home)
    print(f"wrote {args.write}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
