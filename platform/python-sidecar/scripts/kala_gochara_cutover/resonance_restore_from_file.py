"""Restore gochara_resonance_map's chart partition from a CERTIFIED FILE
BACKUP — Pravāha B6.0 PART 0 (native decision 2026-10-01, steward
M20261001T125637-9b2b).

Why this exists: the resonance rebuild's §1 snapshot cannot be a TABLE —
data-plane hardening leaves no reachable role that can CREATE in schema
public (even Cloud SQL 'postgres' gets 'permission denied for schema
public'). The native therefore chose a certified file backup:
`<name>.jsonl` — one `row_to_json(t)::text` line per row, ordered by id,
765 lines for the canonical chart — plus `<name>.jsonl.sha256`. The md5 of
the lines joined by '\\n' IS the runbook's full-row preimage certificate
(the same serialisation the SQL certificate computes), so a file-side
certificate and a live-side certificate can be compared exactly.

REFUSE-UNLESS-VERIFIED, before any DELETE (every check, never a subset):
  1. the file's sha256 equals the first token of `<file>.sha256`;
  2. the line count equals the recorded count (> 0) and the md5 of the
     lines joined by '\\n' equals the recorded full-row digest;
  3. every line parses as one JSON object, carries an `id`, and its
     `chart_id` IS the chart being restored (no foreign row, ever);
  4. the recorded pair itself is sane (positive count, md5 hex — a
     nonempty partition never digests to 'empty').

Then ONE transaction:
  - the sequence guard, BEFORE any DELETE: `last_value` of
    `gochara_resonance_map_id_seq` must be >= the greatest restored id.
    Restored ids were originally issued by this sequence and sequences
    never go backwards, so a conforming backup can never collide with a
    later writer insert; the check refuses a foreign hand-crafted file
    whose ids outrun the sequence. (The restore deliberately does NOT
    setval: the restore role has USAGE on the sequence, never UPDATE —
    steward-verified on production 2026-10-01, and no re-anchoring is
    needed under the never-backwards invariant.);
  - every OTHER chart's full-row certificate is taken (the untouched
    proof baseline);
  - DELETE the chart's partition; INSERT each file row via
    `json_populate_record(NULL::gochara_resonance_map, line)` — the exact
    preimage, ids and computed_at included;
  - the live full-row certificate is recomputed: unless it equals the
    recorded pair the transaction ROLLS BACK (any RAISE leaves the
    partition untouched);
  - every other chart's certificate is re-taken and MUST be unchanged.

DSN: the environment variable RESONANCE_RESTORE_DATABASE_URL only — never
an argv value, never printed, never logged. Restore role:
data_plane_builder (DELETE/INSERT on the table, USAGE on the id sequence;
no triggers on the table).

Default is DRY-RUN: the whole procedure runs inside the transaction and is
then deliberately rolled back — a full dress rehearsal against the real
endpoint that commits nothing. `--execute` commits.

Usage:
  RESONANCE_RESTORE_DATABASE_URL=... python3 resonance_restore_from_file.py \
      --chart-id 482012f1-710e-4a25-994a-93821f5871aa \
      --file /path/gochara_resonance_map_482012f1_20261001071822.jsonl \
      --expect-count 765 --expect-md5 3d270ef0a2db00b240a2acb4d45171c0 [--execute]

Exit codes: 0 restored (or dry-run verified); 1 REFUSED (verification or
post-restore certificate); 2 usage error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

DSN_ENV = "RESONANCE_RESTORE_DATABASE_URL"
_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
_MD5_RE = re.compile(r"^[0-9a-f]{32}$")

FULL_ROW_CERTIFICATE_SQL = (
    "SELECT COUNT(*) AS row_count,\n"
    "       COALESCE(md5(string_agg(row_to_json(t)::text, E'\\n' ORDER BY t.id)), 'empty') AS full_row_digest\n"
    "  FROM gochara_resonance_map t\n"
    " WHERE t.chart_id = %s;"
)

# The exact command lines the production runbook's file-mode variant quotes
# (the drift guard in tests/l3/test_resonance_restore_from_file.py holds the
# runbook to this text).
RUNBOOK_USAGE = """\
  RESONANCE_RESTORE_DATABASE_URL=<data_plane_builder dsn; env only, never argv, never printed> \\
  python3 resonance_restore_from_file.py \\
      --chart-id 482012f1-710e-4a25-994a-93821f5871aa \\
      --file gochara_resonance_map_482012f1_<stamp>.jsonl \\
      --expect-count <count recorded at backup> --expect-md5 <full-row digest recorded at backup> [--execute]"""


class Refusal(Exception):
    """A verification failed — nothing was deleted, nothing was committed."""


def _check_chart(chart_id: str) -> str:
    cid = chart_id.lower()
    if not _UUID_RE.match(cid):
        raise Refusal(f"not a chart uuid: {chart_id!r}")
    return cid


def _check_recorded_pair(expect_count: int, expect_md5: str) -> tuple[int, str]:
    n = int(expect_count)
    if n <= 0:
        raise Refusal("the recorded count must be positive — an empty backup is never a restore anchor")
    digest = expect_md5.lower()
    if not _MD5_RE.match(digest):
        raise Refusal("the recorded full-row digest must be an md5 hex "
                      "(a nonempty partition never digests to 'empty')")
    return n, digest


def read_sha256_sidecar(file_path: str) -> str:
    """The expected sha256 hex: the first whitespace-separated token of
    `<file>.sha256` (the coreutils `sha256sum` format)."""
    sidecar = file_path + ".sha256"
    try:
        with open(sidecar, "r", encoding="utf-8") as fh:
            token = fh.read().split()[0].lower()
    except (OSError, IndexError) as exc:
        raise Refusal(f"cannot read the sha256 sidecar {sidecar!r}: {exc}")
    if not re.fullmatch(r"[0-9a-f]{64}", token):
        raise Refusal(f"sha256 sidecar {sidecar!r} does not carry a sha256 hex token")
    return token


def load_and_verify_file(file_path: str, chart_id: str,
                         expect_count: int, expect_md5: str) -> list[str]:
    """Controls 1-3: sha256, count + joined-md5, per-row chart uniformity.
    Returns the file's lines (without newlines) on success; Refusal otherwise."""
    cid = _check_chart(chart_id)
    n, digest = _check_recorded_pair(expect_count, expect_md5)
    try:
        with open(file_path, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        raise Refusal(f"cannot read the backup file {file_path!r}: {exc}")
    actual_sha = hashlib.sha256(raw).hexdigest()
    expected_sha = read_sha256_sidecar(file_path)
    if actual_sha != expected_sha:
        raise Refusal(f"RESTORE REFUSED: sha256 of {file_path!r} is {actual_sha}, "
                      f"the sidecar says {expected_sha}")
    text = raw.decode("utf-8")
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()  # one trailing newline terminates the last line; it is not a row
    if any(line == "" for line in lines):
        raise Refusal("RESTORE REFUSED: the backup file carries a blank line")
    if len(lines) != n:
        raise Refusal(f"RESTORE REFUSED: the backup carries {len(lines)} rows, "
                      f"the recorded count is {n}")
    joined_md5 = hashlib.md5("\n".join(lines).encode("utf-8")).hexdigest()
    if joined_md5 != digest:
        raise Refusal(f"RESTORE REFUSED: the backup's joined-md5 is {joined_md5}, "
                      f"the recorded full-row digest is {digest}")
    seen_ids: set[int] = set()
    for i, line in enumerate(lines, 1):
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise Refusal(f"RESTORE REFUSED: line {i} is not JSON ({exc})")
        if not isinstance(row, dict):
            raise Refusal(f"RESTORE REFUSED: line {i} is not a JSON object")
        if row.get("chart_id") != cid:
            raise Refusal(f"RESTORE REFUSED: line {i} carries chart_id "
                          f"{row.get('chart_id')!r} — a foreign row is never restored")
        rid = row.get("id")
        if not isinstance(rid, int):
            raise Refusal(f"RESTORE REFUSED: line {i} carries no integer id")
        if rid in seen_ids:
            raise Refusal(f"RESTORE REFUSED: id {rid} appears twice in the backup")
        seen_ids.add(rid)
    return lines


def other_chart_certificates(cur, chart_id: str) -> dict[str, tuple[int, str]]:
    """Full-row certificate of every OTHER chart present (the untouched
    proof baseline)."""
    cur.execute(
        "SELECT t.chart_id::text, COUNT(*),\n"
        "       COALESCE(md5(string_agg(row_to_json(t)::text, E'\\n' ORDER BY t.id)), 'empty')\n"
        "  FROM gochara_resonance_map t WHERE t.chart_id <> %s GROUP BY t.chart_id;",
        (chart_id,))
    return {row[0]: (int(row[1]), row[2]) for row in cur.fetchall()}


def certificate(cur, chart_id: str) -> tuple[int, str]:
    cur.execute(FULL_ROW_CERTIFICATE_SQL, (chart_id,))
    row = cur.fetchone()
    return (int(row[0]), row[1])


def restore(conn, chart_id: str, lines: list[str],
            expect_count: int, expect_md5: str, execute: bool) -> dict:
    """The one-transaction restore. `conn` is psycopg (autocommit False).
    Returns a result dict; raises Refusal (transaction already rolled back
    by the context manager) on any violated certificate."""
    cid = _check_chart(chart_id)
    n, digest = _check_recorded_pair(expect_count, expect_md5)
    with conn.transaction():
        cur = conn.cursor()
        # The sequence guard, BEFORE any DELETE: sequences never go
        # backwards, so the backup's greatest id must not outrun the
        # sequence. USAGE on the sequence (the restore role's exact grant)
        # suffices to read last_value; no setval is needed or possible.
        max_restored_id = max(json.loads(line)["id"] for line in lines)
        # pg_sequences (not a direct sequence read): SELECT on the sequence
        # itself is NOT among the restore role's grants — USAGE is, and
        # pg_sequences exposes last_value under USAGE. NULL = never read ⇒ 0.
        cur.execute(
            "SELECT COALESCE(last_value, 0) FROM pg_sequences\n"
            " WHERE schemaname = 'public' AND sequencename = 'gochara_resonance_map_id_seq';")
        row = cur.fetchone()
        if row is None:
            raise Refusal("RESTORE REFUSED: gochara_resonance_map_id_seq is absent")
        last_value = int(row[0])
        if last_value < max_restored_id:
            raise Refusal(
                f"RESTORE REFUSED: the backup's greatest id {max_restored_id} outruns "
                f"gochara_resonance_map_id_seq last_value {last_value} — a foreign "
                "hand-crafted file is never a restore anchor")
        before_others = other_chart_certificates(cur, cid)
        cur.execute("DELETE FROM gochara_resonance_map WHERE chart_id = %s;", (cid,))
        for line in lines:
            cur.execute(
                "INSERT INTO gochara_resonance_map\n"
                "SELECT * FROM json_populate_record(NULL::gochara_resonance_map, %s::json);",
                (line,))
        live_count, live_digest = certificate(cur, cid)
        if live_count != n or live_digest != digest:
            raise Refusal(
                f"RESTORE FAILED VERIFICATION: restored certificate "
                f"({live_count}, {live_digest}) vs recorded ({n}, {digest}) — rolled back")
        after_others = other_chart_certificates(cur, cid)
        if after_others != before_others:
            raise Refusal("RESTORE FAILED VERIFICATION: another chart's partition changed — rolled back")
        result = {
            "chart_id": cid, "rows": live_count, "full_row_digest": live_digest,
            "other_charts_untouched": len(before_others),
            "committed": bool(execute),
        }
        if not execute:
            raise _DryRunComplete(result)
        return result


class _DryRunComplete(Exception):
    def __init__(self, result: dict):
        super().__init__("dry-run: verified, rolled back")
        self.result = result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Restore gochara_resonance_map's chart partition from a certified "
                    "file backup (refuse-unless-verified; DSN from the environment only).")
    parser.add_argument("--chart-id", required=True)
    parser.add_argument("--file", required=True, help="the .jsonl backup; its sha256 sidecar is <file>.sha256")
    parser.add_argument("--expect-count", required=True, type=int,
                        help="the row count recorded when the backup was certified")
    parser.add_argument("--expect-md5", required=True,
                        help="the full-row digest recorded when the backup was certified")
    parser.add_argument("--execute", action="store_true",
                        help="commit; without it the whole procedure runs and ROLLS BACK (dress rehearsal)")
    args = parser.parse_args(argv)

    dsn = os.environ.get(DSN_ENV)
    if not dsn:
        print(f"ERROR: no DSN — set {DSN_ENV} (never pass a DSN on the command line)", file=sys.stderr)
        return 2
    try:
        lines = load_and_verify_file(args.file, args.chart_id, args.expect_count, args.expect_md5)
    except Refusal as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"file verified: {len(lines)} rows, certificate "
          f"({args.expect_count}, {args.expect_md5.lower()}) — proceeding to the transactional restore")

    import psycopg  # deferred so --help works without the driver
    try:
        with psycopg.connect(dsn, connect_timeout=10) as conn:
            try:
                result = restore(conn, args.chart_id, lines,
                                 args.expect_count, args.expect_md5, args.execute)
            except _DryRunComplete as done:
                result = done.result
                print("DRY-RUN verified — transaction rolled back, nothing committed:")
                print(json.dumps(result, indent=2))
                return 0
    except Refusal as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("RESTORED and certificate-verified:" if result["committed"] else "verified:")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
