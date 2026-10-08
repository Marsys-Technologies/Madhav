"""Process entry point for the separately dispatched candidate verifier."""

from __future__ import annotations

import argparse
import os

import psycopg

from services.kala_core.manifest import Candidate
from services.kala_core.verify import verify_candidate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chart-id", required=True)
    parser.add_argument("--generation", required=True)
    parser.add_argument("--build-id", required=True)
    parser.add_argument("--expected-head")
    parser.add_argument("--independently-derived-digest", required=True)
    args = parser.parse_args()
    dsn = os.environ["KALA_VERIFIER_DSN"]
    candidate = Candidate(args.chart_id, args.generation, args.build_id, args.expected_head)
    with psycopg.connect(dsn) as conn:
        independently_derived = args.independently_derived_digest
        verify_candidate(conn, candidate, independently_derived_digest=independently_derived)
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised by the dispatch boundary
    raise SystemExit(main())
