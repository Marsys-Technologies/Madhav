"""Offline arithmetic review for a separately authorized F-184 regeneration.

Reads an explicitly supplied GROUNDED_SIGNALS JSON mapping. Never loads a chart,
MSR corpus, credentials, database or embedding provider, and never writes facts.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections.abc import Mapping
from typing import Any, BinaryIO

MAX_JSON_BYTES = 8 * 1024 * 1024


def confidence_summary(signals: Mapping[str, Mapping[str, Any]], *, expected_count: int) -> dict[str, int | float]:
    """Report only count/mean; incomplete confidence never becomes a default."""
    if type(expected_count) is not int or expected_count <= 0:
        raise ValueError("expected_count")
    if not isinstance(signals, Mapping) or len(signals) != expected_count:
        raise ValueError("signal_count")
    values = []
    for signal_id, row in signals.items():
        if not isinstance(signal_id, str) or not signal_id or not isinstance(row, Mapping):
            raise ValueError("signal_shape")
        value = row.get("match_confidence")
        if type(value) not in (int, float) or not 0 <= value <= 1 or not math.isfinite(value):
            raise ValueError("match_confidence")
        values.append(float(value))
    return {"signal_count": len(values), "mean_match_confidence": math.fsum(values) / len(values)}


def _unique(pairs):
    result = dict(pairs)
    if len(result) != len(pairs):
        raise ValueError("duplicate_key")
    return result


def _reject_constant(_value):
    raise ValueError("constant")


def main(argv=None, *, stdin: BinaryIO | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-count", type=int, required=True)
    args = parser.parse_args(argv)
    stream = sys.stdin.buffer if stdin is None else stdin
    try:
        raw = stream.read(MAX_JSON_BYTES + 1)
        if len(raw) > MAX_JSON_BYTES:
            raise ValueError("input_size")
        signals = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique,
                             parse_constant=_reject_constant)
        result = confidence_summary(signals, expected_count=args.expected_count)
    except (ValueError, TypeError, UnicodeError, OverflowError, RecursionError):
        # No source text, signal identifiers, exception messages or input hashes.
        print(json.dumps({"error": "invalid_confidence_input"}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
