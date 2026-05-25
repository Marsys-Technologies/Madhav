#!/usr/bin/env python3
"""
generate_derivation_ledger_stubs.py

Generates derivation_ledger stub blocks for MSR v5.0 signals that lack them.

Usage:
  python3 generate_derivation_ledger_stubs.py \\
      --source 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md \\
      [--dry-run] \\
      [--output <path>]

The script parses all SIG.MSR.NNN signal blocks from the MSR markdown file,
identifies signals that lack a `derivation_ledger:` block, and injects a
PENDING stub block immediately after the last field of each ungrounded signal.

The stub takes the form:
  derivation_ledger:
    l1_sources: []  # TODO: fill with FORENSIC v6_id references
    grounding_status: PENDING
    grounded_by: ~
    grounded_date: ~

In --dry-run mode, prints a summary to stdout and exits without writing files.
In normal mode, writes the updated MSR file to --output (defaults to --source).
"""

import argparse
import re
import sys
from pathlib import Path

# ── Patterns ──────────────────────────────────────────────────────────────────

# A signal header line: "SIG.MSR.NNN:" at column 0
SIGNAL_HEADER_RE = re.compile(r'^(SIG\.MSR\.\d+):')

# A derivation_ledger key at any indentation level
DERIVATION_LEDGER_RE = re.compile(r'^\s+derivation_ledger\s*:')

# The stub to inject (4-space indent to match MSR YAML field style)
STUB_LINES = [
    "  derivation_ledger:",
    "    l1_sources: []  # TODO: fill with FORENSIC v6_id references",
    "    grounding_status: PENDING",
    "    grounded_by: ~",
    "    grounded_date: ~",
]


# ── Signal boundary parser ────────────────────────────────────────────────────

def parse_signal_blocks(lines: list[str]) -> list[dict]:
    """
    Walk the MSR line list and return a list of signal block descriptors:
      {
        'signal_id': 'SIG.MSR.001',
        'start': <line index of header>,
        'end': <exclusive line index — first line of next signal or EOF>,
        'has_derivation_ledger': bool,
      }
    """
    signals: list[dict] = []
    current: dict | None = None

    for idx, line in enumerate(lines):
        m = SIGNAL_HEADER_RE.match(line)
        if m:
            # Close out the previous signal
            if current is not None:
                current['end'] = idx
                signals.append(current)
            current = {
                'signal_id': m.group(1),
                'start': idx,
                'end': None,
                'has_derivation_ledger': False,
            }
        elif current is not None:
            if DERIVATION_LEDGER_RE.match(line):
                current['has_derivation_ledger'] = True

    # Close last signal
    if current is not None:
        current['end'] = len(lines)
        signals.append(current)

    return signals


# ── Stub injector ─────────────────────────────────────────────────────────────

def find_last_content_line(lines: list[str], start: int, end: int) -> int:
    """
    Within lines[start:end], return the index of the last non-empty line.
    This is where we'll insert the stub (after this line).
    """
    last = start
    for i in range(start, end):
        if lines[i].rstrip():
            last = i
    return last


def inject_stubs(lines: list[str], signals: list[dict]) -> tuple[list[str], int]:
    """
    Return (new_lines, stubs_generated) with stub blocks injected after
    each ungrounded signal's last content line.

    We process signals in reverse order so that earlier insertion points
    are not shifted by later insertions.
    """
    stubs_generated = 0
    ungrounded = [s for s in signals if not s['has_derivation_ledger']]

    # Sort descending by start line so reverse-order insertion is stable
    for sig in sorted(ungrounded, key=lambda s: s['start'], reverse=True):
        insert_after = find_last_content_line(lines, sig['start'], sig['end'])
        insert_at = insert_after + 1  # insert after the last content line
        stub_block = [l + "\n" for l in STUB_LINES] + ["\n"]
        lines = lines[:insert_at] + stub_block + lines[insert_at:]
        stubs_generated += 1

    return lines, stubs_generated


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate derivation_ledger stub blocks for ungrounded MSR signals."
    )
    parser.add_argument(
        "--source",
        default="025_HOLISTIC_SYNTHESIS/MSR_v5_0.md",
        help="Path to MSR_v5_0.md (default: 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print stats only; do not write any files.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output path (default: overwrite --source).",
    )
    args = parser.parse_args()

    source_path = Path(args.source)
    if not source_path.exists():
        print(f"ERROR: source file not found: {source_path}", file=sys.stderr)
        sys.exit(1)

    lines = source_path.read_text(encoding="utf-8").splitlines(keepends=True)

    signals = parse_signal_blocks(lines)
    total_signals = len(signals)
    already_grounded = sum(1 for s in signals if s['has_derivation_ledger'])
    stubs_needed = total_signals - already_grounded

    if args.dry_run:
        print(f"stubs_generated: {stubs_needed}")
        print(f"already_grounded: {already_grounded}")
        print(f"total_signals: {total_signals}")
        return

    # Normal mode: inject stubs and write
    new_lines, stubs_generated = inject_stubs(lines, signals)

    output_path = Path(args.output) if args.output else source_path
    output_path.write_text("".join(new_lines), encoding="utf-8")

    print(f"stubs_generated: {stubs_generated}")
    print(f"already_grounded: {already_grounded}")
    print(f"total_signals: {total_signals}")
    print(f"written_to: {output_path}")


if __name__ == "__main__":
    main()
