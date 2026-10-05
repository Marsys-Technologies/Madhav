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
    said = sb._policy_disclosure("all_null_candidate/1")
    assert said == sb.ALL_NULL_DISCLOSURE and "no numerical result exists" not in said
    assert said == ("The result policy `all_null_candidate/1` forbids any numerical result or qualified valence in every record, window and "
                    "window-membership link of this generation, and the gate refuses legacy projection rows for it (`record_result_not_policy`, "
                    "`legacy_projection_rows_present`); this is a property the gate enforces at seal, not a property of the database's contents "
                    "at every moment.")                                                           # VERBATIM packet §R13b (F-R14-1)
    import pathlib
    gate = (pathlib.Path(__file__).resolve().parents[4] / "migrations" / "1240_gochara_window_verification_gate.sql").read_text()
    assert "'record_result_not_policy'" in gate and "'legacy_projection_rows_present'" in gate     # the two refusal names the sentence cites
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
    assert set(compact) == {"status", "contract_version", "sha256", "persisted", "producer", "brief_bytes", "brief_file", "brief_chunks"}
    assert compact["contract_version"] == "seal_brief_transport/1" and set(compact["producer"]) == {"commit", "image_digest", "execution_id"}
    assert compact["status"] == "BRIEFED" and compact["brief_file"] is None and compact["brief_chunks"] is True
    raw = sb.reassemble_chunks(chunk_lines)
    assert len(raw) == compact["brief_bytes"] and hashlib.sha256(raw).hexdigest() == compact["sha256"]
    brief = json.loads(raw)
    assert sb.payload_digest(json.loads(raw, parse_float=Decimal)) == compact["sha256"]
    assert compact["persisted"]["manifest_id"] == brief["manifest"]["manifest_id"] and compact["persisted"]["brief_id"] > 0
    assert re.fullmatch(r"[0-9a-f]{64}", compact["persisted"]["state_digest"])


# ── the Cloud Run LOG-ENTRY shape (R13-1, Stream A's half) ───────────────────────────────────────────────────────────
# Cloud Run parses a JSON OBJECT written to stdout into the ROOT of the entry's `jsonPayload` (not `textPayload`, not `jsonPayload.message`).
# Each chunk line and the compact line is therefore ONE entry whose jsonPayload IS the line's object. Consequences the reader must respect:
# (1) the entry's text is NOT preserved — jsonPayload is a protobuf Struct (a map): key order is lost, so nothing may depend on the line's bytes
#     (the chunk design carries its integrity in `sha256` + base64 `b64`, never in the printed text); (2) every JSON number becomes a double
#     (3 -> 3.0), so integers are read through int(); (3) Cloud Logging delivers at least once, so duplicates are possible and an identical
#     repeat of an index is harmless; (4) arrival order is not guaranteed. The fixture is built from Google's documented LogEntry fields for a
#     `cloud_run_job` resource from the REAL golden stdout — it is NOT a capture from Cloud Run.

LOG_ENTRIES = Path(__file__).parent / "fixtures" / "golden_brief_log_entries_1class.json"


def _read_brief_from_log_entries(entries: list[dict]) -> tuple[bytes, dict]:
    """The reader side of the structured-log transport: (brief bytes, the compact result)."""
    chunks, compact = {}, None
    for e in entries:
        p = e.get("jsonPayload")
        if not isinstance(p, dict):
            continue
        if "brief_chunk" in p:
            i, n = int(p["brief_chunk"]), int(p["of"])
            if i in chunks and chunks[i] != (n, p["sha256"], p["b64"]):
                raise ValueError(f"two different chunks carry index {i}")
            chunks[i] = (n, p["sha256"], p["b64"])
        elif p.get("status") == "BRIEFED":
            assert p.get("contract_version") == "seal_brief_transport/1", "a compact entry with a missing or unknown contract_version is refused"
            compact = p
    assert compact is not None and chunks
    total = {n for n, _, _ in chunks.values()}
    assert len(total) == 1 and sorted(chunks) == list(range(total.pop())), "chunks missing or inconsistent"
    raw = b"".join(base64.b64decode(chunks[i][2]) for i in sorted(chunks))
    assert {s for _, s, _ in chunks.values()} == {compact["sha256"]}
    assert hashlib.sha256(raw).hexdigest() == compact["sha256"] and len(raw) == int(compact["brief_bytes"])
    return raw, compact


def test_the_structured_log_fixture_is_the_golden_stdout_as_cloud_run_entries_and_reassembles():
    entries = json.loads(LOG_ENTRIES.read_text())
    golden = [json.loads(x) for x in GOLDEN.read_text().splitlines()]
    assert [e["jsonPayload"] for e in entries] == golden                                # one entry per stdout line, the object at the ROOT
    assert all("textPayload" not in e and "message" not in e["jsonPayload"] for e in entries)
    assert {e["resource"]["type"] for e in entries} == {"cloud_run_job"}
    raw, compact = _read_brief_from_log_entries(entries)
    assert sb.reassemble_chunks(GOLDEN.read_text().splitlines()[:-1]) == raw           # the same bytes as the plain stdout route
    assert compact["contract_version"] == "seal_brief_transport/1" and compact["persisted"]["brief_id"] > 0


def test_the_reader_survives_what_cloud_logging_does_to_a_json_payload():
    """Numbers as doubles, key order lost, duplicates, arrival order scrambled — and a conflicting duplicate refused."""
    entries = json.loads(LOG_ENTRIES.read_text())

    def doublify(v):
        if isinstance(v, bool) or v is None or isinstance(v, str):
            return v
        if isinstance(v, int):
            return float(v)
        if isinstance(v, dict):
            return {k: doublify(v[k]) for k in sorted(v, reverse=True)}                  # (key order is not preserved either)
        return [doublify(x) for x in v]
    mangled = [{**e, "jsonPayload": doublify(e["jsonPayload"])} for e in reversed(entries)]
    mangled = mangled + mangled[:2]                                                       # at-least-once delivery: duplicates
    raw, compact = _read_brief_from_log_entries(mangled)
    assert hashlib.sha256(raw).hexdigest() == compact["sha256"]
    bad = json.loads(json.dumps(next(e for e in mangled if "brief_chunk" in e["jsonPayload"])))
    bad["jsonPayload"]["b64"] = base64.b64encode(b"tampered").decode()
    with pytest.raises(ValueError, match="two different chunks"):
        _read_brief_from_log_entries(mangled + [bad])
