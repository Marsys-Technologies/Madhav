"""A5.3 — independent review F-R13-6 and F-R13-2: the brief's serializer and its transport.

F-R13-6: the brief print used `json.dumps(..., default=str)`: any type the author did not foresee would have been stringified silently. The
brief (and its digest) are now written by ONE strict canonical serializer that encodes each type by an explicit rule and REFUSES the rest.
F-R13-2: the full brief grows with the event-class count (~255 KB at 26 classes), so stdout ends in a compact line and the brief travels by
file or index/total chunk lines whose reassembly must hash to the persisted digest."""
from __future__ import annotations

import base64
import datetime as dt
import hashlib
import json
import re
import uuid
from decimal import Decimal
from pathlib import Path

import pytest

from services.gochara_kernel import seal_brief as sb
from services.gochara_kernel import window_gate as wg

ROOT = Path(__file__).resolve().parents[3]


# ── F-R13-6: explicit rules, everything else refused ─────────────────────────────────────────────────────────────

def test_each_type_the_brief_can_carry_has_an_explicit_tested_rule():
    assert sb.canonical_json(None) == "null" and sb.canonical_json(True) == "true" and sb.canonical_json(False) == "false"
    assert sb.canonical_json(7) == "7" and sb.canonical_json(-3) == "-3"
    assert sb.canonical_json(Decimal("1E+2")) == "100" and sb.canonical_json(Decimal("-0.50")) == "-0.50"
    assert sb.canonical_json(Decimal("12345678901234567890.123456789")) == "12345678901234567890.123456789"   # no float round trip
    u = uuid.UUID("AAAAAAAA-BBBB-4CCC-8DDD-EEEEEEEEEEEE")
    assert sb.canonical_json(u) == '"aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"'
    kolkata = dt.timezone(dt.timedelta(hours=5, minutes=30))
    assert sb.canonical_json(dt.datetime(2026, 10, 2, 15, 30, 1, 5, tzinfo=kolkata)) == '"2026-10-02T10:00:01.000005Z"'
    assert sb.canonical_json(dt.datetime(2026, 10, 2, 10, 0, tzinfo=dt.timezone.utc)) == '"2026-10-02T10:00:00.000000Z"'
    assert sb.canonical_json(dt.date(2026, 10, 2)) == '"2026-10-02"'
    assert sb.canonical_json({"b": [1, (2, 3)], "a": "ṣaḍbala — é"}) == '{"a":"ṣaḍbala — é","b":[1,[2,3]]}'   # sorted, compact, unescaped


class _Oddity:
    def __str__(self):
        return "str() must never be what gets hashed"


@pytest.mark.parametrize("value,why", [
    (1.5, "float"), (float("nan"), "float"), (b"bytes", "bytes"), ({1, 2}, "set"), (_Oddity(), "_Oddity"),
    (Decimal("NaN"), "non-finite"), (Decimal("Infinity"), "non-finite"), (Decimal("-Infinity"), "non-finite"),
    (dt.datetime(2026, 10, 2, 10, 0), "naive datetime"), (range(3), "range"), (dt.timedelta(days=1), "timedelta"),
    ({1: "x"}, "keys must be strings"), ({"a": {"b": [1, {"c": 2.0}]}}, "float"),
])
def test_every_other_type_is_refused_naming_where(value, why):
    with pytest.raises(sb.NotCanonicallyEncodable, match=re.escape(why)) as exc:
        sb.canonical_json(value)
    assert "$" in str(exc.value)
    with pytest.raises(sb.NotCanonicallyEncodable):                 # the payload digest cannot be computed over it either
        sb.payload_digest({"x": value})


def test_the_refusal_names_the_path_of_the_offender():
    with pytest.raises(sb.NotCanonicallyEncodable, match=re.escape("$.classes[1].grains[0].verified_at")):
        sb.canonical_json({"classes": [{}, {"grains": [{"verified_at": 1.25}]}]})


def test_for_every_type_the_digest_form_already_used_the_bytes_are_identical_to_window_gate_canon():
    """No existing digest moves: the strict serializer reproduces `window_gate._canon` byte for byte on everything that one encoded."""
    doc = {"z": [None, True, False, 0, -5, 10 ** 30, Decimal("0.10"), Decimal("1E-7"), "q\"uote\\ \n\ttab", "ṣ—é𝔘"],
           "a": {"nested": {"k": [], "j": {}}, "": "empty key"}, "m": (1, (2, 3))}
    assert sb.canonical_json(doc) == wg._canon(doc)


def test_the_display_and_the_digest_share_one_serializer_and_the_brief_path_has_no_default_str():
    import inspect
    from pipeline.orchestrator import verification_job as entry
    src = inspect.getsource(sb)
    assert "default=str" not in src and sb._canon is sb.canonical_json
    main = inspect.getsource(entry.main)
    brief_block = main[main.index("if args.brief:"):main.index("report = vj.run(")]
    assert "default=str" not in brief_block and "json.dumps" not in brief_block        # everything printed goes through canonical_json
    payload = {"schema": "x", "n": Decimal("3.50")}
    assert sb.payload_digest(payload) == hashlib.sha256(sb.canonical_json(payload).encode()).hexdigest()


# ── F-R13-2: the chunked transport ──────────────────────────────────────────────────────────────────────────────

RAW = sb.canonical_json({"schema": "seal_approval_payload/1", "rows": [f"row {i} ṣaḍbala — " * 20 for i in range(300)]}).encode("utf-8")
DIGEST = hashlib.sha256(RAW).hexdigest()


@pytest.mark.parametrize("size", [7, 1000, 4096, len(RAW) - 1, len(RAW), len(RAW) + 5, sb.CHUNK_RAW_BYTES])
def test_the_chunks_reassemble_to_the_exact_bytes_whatever_the_chunk_size(size):
    lines = sb.brief_chunk_lines(RAW, DIGEST, size)
    assert sb.reassemble_chunks(lines) == RAW
    assert all(len(x) < size * 4 // 3 + 200 for x in lines)                              # a chunk line is bounded by the chunk size


def test_one_byte_chunks_and_an_empty_brief_round_trip():
    tiny = b'{"a":"b"}'
    assert sb.reassemble_chunks(sb.brief_chunk_lines(tiny, hashlib.sha256(tiny).hexdigest(), 1)) == tiny
    assert sb.reassemble_chunks(sb.brief_chunk_lines(b"", hashlib.sha256(b"").hexdigest())) == b""
    with pytest.raises(ValueError):
        sb.brief_chunk_lines(tiny, "0" * 64, 0)


def test_every_chunk_line_is_small_and_one_json_object_so_a_log_entry_limit_cannot_truncate_the_brief():
    big = sb.canonical_json({"rows": ["x" * 1000 for _ in range(400)]}).encode()        # ~400 KB, beyond a 256 KB log entry
    lines = sb.brief_chunk_lines(big, hashlib.sha256(big).hexdigest())
    assert len(lines) >= 8 and max(len(x) for x in lines) < 70 * 1024
    assert sb.reassemble_chunks(lines) == big
    assert all(json.loads(x)["of"] == len(lines) for x in lines)


def test_reassembly_refuses_missing_duplicated_foreign_and_tampered_chunks():
    lines = sb.brief_chunk_lines(RAW, DIGEST, 2048)
    assert len(lines) > 3
    with pytest.raises(sb.BriefRefused, match="chunks_incomplete"):
        sb.reassemble_chunks(lines[:-1])
    with pytest.raises(sb.BriefRefused, match="chunks_incomplete"):
        sb.reassemble_chunks(lines + [lines[0]])
    other = sb.brief_chunk_lines(b'{"a":1}', hashlib.sha256(b'{"a":1}').hexdigest(), 2048)
    with pytest.raises(sb.BriefRefused, match="chunks_incomplete"):
        sb.reassemble_chunks(lines[:-1] + other)
    forged = json.loads(lines[1])
    forged["b64"] = base64.b64encode(b"tampered").decode()
    with pytest.raises(sb.BriefRefused, match="chunks_digest_mismatch"):
        sb.reassemble_chunks([lines[0], sb.canonical_json(forged)] + lines[2:])
    with pytest.raises(sb.BriefRefused, match="no_chunks"):
        sb.reassemble_chunks([])
    assert sb.reassemble_chunks(list(reversed(lines))) == RAW                           # order on the wire does not matter


def test_the_brief_bytes_must_hash_to_the_digest_they_carry():
    payload = {"schema": "x", "v": [1, 2]}
    good = {"payload": payload, "sha256": sb.payload_digest(payload)}
    assert sb.brief_bytes(good) == sb.canonical_json(payload).encode()
    with pytest.raises(sb.BriefRefused, match="brief_bytes_digest_mismatch"):
        sb.brief_bytes({"payload": payload, "sha256": "0" * 64})


# ── disclosure wording follows the manifest's policy (Stream B request) ─────────────────────────────────────────────

def test_the_disclosure_names_the_manifest_policy_and_claims_all_null_only_under_it():
    assert sb._policy_disclosure("all_null_candidate/1").startswith("all_null_candidate/1 — no numerical result exists")
    other = sb._policy_disclosure("window_qualification/1")
    assert other.startswith("window_qualification/1") and "no numerical result" not in other and "no all-NULL claim" in other


# ── the GOLDEN stdout of the real job (for Stream B's extractor tests) ───────────────────────────────────────────────

GOLDEN = Path(__file__).parent / "fixtures" / "golden_brief_stdout_1class.txt"


def test_the_golden_stdout_is_chunk_lines_then_a_compact_line_that_reassemble_to_the_digest():
    """`fixtures/golden_brief_stdout_1class.txt` is the REAL stdout of `verification_job --brief --brief-chunk-bytes 8192` for the 1-class
    faithful world (regenerate: GOCHARA_WRITE_GOLDEN_BRIEF=<path> pytest tests/l3/gochara/test_a53_r11_seal_brief.py -k entry_points)."""
    lines = GOLDEN.read_text().splitlines()
    chunk_lines, compact = lines[:-1], json.loads(lines[-1])
    assert len(chunk_lines) >= 3 and all(set(json.loads(x)) == {"brief_chunk", "of", "sha256", "b64"} for x in chunk_lines)
    assert set(compact) == {"status", "sha256", "persisted", "brief_bytes", "brief_file", "brief_chunks"}
    assert compact["status"] == "BRIEFED" and compact["brief_file"] is None and compact["brief_chunks"] is True
    raw = sb.reassemble_chunks(chunk_lines)
    assert len(raw) == compact["brief_bytes"] and hashlib.sha256(raw).hexdigest() == compact["sha256"]
    brief = json.loads(raw)
    assert sb.payload_digest(json.loads(raw, parse_float=Decimal)) == compact["sha256"]
    assert compact["persisted"]["manifest_id"] == brief["manifest"]["manifest_id"] and compact["persisted"]["brief_id"] > 0
    assert re.fullmatch(r"[0-9a-f]{64}", compact["persisted"]["state_digest"])
