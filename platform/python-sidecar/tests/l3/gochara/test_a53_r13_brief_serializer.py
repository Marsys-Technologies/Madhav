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


# ── F-R13-2: the transport contract agreed with Stream B ───────────────────────────────────────────────────────────

import importlib.util

_REF_PATH = Path(__file__).parent / "fixtures" / "b6_gochara_seal_brief_extract_reference.py"
_spec = importlib.util.spec_from_file_location("b6_extract_reference", _REF_PATH)
REF = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(REF)


def test_the_display_form_is_ascii_and_equals_json_dumps_with_sorted_keys():
    doc = {"b": ["ṣaḍbala — é𝔘", 1, None], "a": {"z": True, "y": "q\"\n"}}
    assert sb.canonical_json(doc, ascii_only=True) == json.dumps(doc, sort_keys=True, separators=(",", ":"))
    assert sb.canonical_json(doc, ascii_only=True).isascii() and json.loads(sb.canonical_json(doc, ascii_only=True)) == doc
    assert not sb.canonical_json(doc).isascii()                                      # (the digest form stays unescaped)


def _result(payload):
    return {"payload": payload, "sha256": sb.payload_digest(payload)}


PERSISTED = {"brief_id": 3, "manifest_id": "11111111-2222-4333-8444-555555555555", "state_digest": "ab" * 32}


def test_the_brief_line_has_exactly_the_agreed_shape_is_ascii_and_keeps_decimals_exact():
    payload = {"manifest": {"manifest_id": PERSISTED["manifest_id"], "backend": {"orb": Decimal("3.50"), "n": 7}}, "txt": "ṣaḍbala — é"}
    line = sb.brief_line(_result(payload), PERSISTED)
    assert line.startswith('{"brief":') and line.isascii() and "\n" not in line.replace("\\n", "")
    doc = json.loads(line, parse_float=Decimal)
    assert list(doc) == ["brief", "persisted", "sha256"] and doc["persisted"] == PERSISTED         # sorted: brief, persisted, sha256
    assert '"orb":3.50' in line                                                      # not 3.5, not a quoted string
    assert sb.payload_digest(doc["brief"]) == doc["sha256"] == sb.payload_digest(payload)           # the round trip F-R13-6 asks for


def test_the_brief_line_refuses_what_it_cannot_round_trip():
    with pytest.raises(sb.NotCanonicallyEncodable):
        sb.brief_line(_result({"a": 1}) | {"payload": {"a": 1.5}}, PERSISTED)         # a float anywhere in the payload
    with pytest.raises(sb.BriefRefused, match="brief_line_digest_mismatch"):
        sb.brief_line({"payload": {"a": 1}, "sha256": "0" * 64}, PERSISTED)


def _line_of(n):
    """A brief-line-shaped ASCII text of exactly n characters."""
    head = '{"brief":{"pad":"'
    tail = '"},"persisted":{},"sha256":"x"}'
    return head + "p" * (n - len(head) - len(tail)) + tail


def test_a_line_up_to_200000_characters_is_printed_unchanged_and_longer_ones_are_chunked():
    just_under, exactly, just_over = _line_of(199_999), _line_of(200_000), _line_of(200_001)
    assert sb.emit_lines(just_under) == [just_under] and sb.emit_lines(exactly) == [exactly]
    lines = sb.emit_lines(just_over)
    assert len(lines) == 4 and all(len(x) < 60_200 for x in lines)                          # 200,001 chars -> 60,000-char slices
    assert [json.loads(x)["brief_chunk"]["index"] for x in lines] == [0, 1, 2, 3]
    assert {json.loads(x)["brief_chunk"]["total"] for x in lines} == {4}


@pytest.mark.parametrize("text", [_line_of(200_001), _line_of(600_000), _line_of(180_000), _line_of(200_000),
                                  # a multi-byte character straddling a slice boundary (60,000 chars / 120,000 chars)
                                  '{"brief":"' + "é" * 59_990 + "—" + "𝔘" * 30_000 + "ṣ" * 120_000 + 'x"}'])
def test_the_emit_is_identical_to_stream_bs_reference_chunk_brief_and_their_extractor_reassembles_it(text):
    lines = sb.emit_lines(text)
    if len(text) > sb.BRIEF_SINGLE_LINE_MAX:
        assert lines == REF.chunk_brief(text)                                       # byte-for-byte the reference's lines
    else:
        assert lines == [text]
    entries = [{"textPayload": x} for x in reversed(lines)]                          # arrival order is never relied on
    assert REF.extract(entries) == text


def test_a_real_sized_brief_line_travels_through_the_reference_extractor_and_still_rederives_its_digest():
    payload = {"schema": "seal_approval_payload/1", "classes": [{"event_class": f"c{i}", "pad": "ṣaḍbala — é" * 700} for i in range(26)]}
    line = sb.brief_line(_result(payload), PERSISTED)
    assert len(line) > sb.BRIEF_SINGLE_LINE_MAX                                          # forces the chunked route
    lines = sb.emit_lines(line)
    assert len(lines) > 1 and all(x.isascii() for x in lines)
    text = REF.extract([{"textPayload": x} for x in lines])
    assert text == line
    doc = json.loads(text, parse_float=Decimal)
    assert sb.payload_digest(doc["brief"]) == doc["sha256"]


def test_the_vendored_reference_has_not_drifted_from_the_platform_script_once_it_is_on_this_branch():
    script = ROOT.parent / "scripts" / "gochara_seal_brief_extract.py"
    if not script.exists():
        pytest.skip("platform/scripts/gochara_seal_brief_extract.py (PR #2975) is not on this branch yet")
    spec = importlib.util.spec_from_file_location("b6_extract_live", script)
    live = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(live)
    text = _line_of(250_000)
    assert live.chunk_brief(text) == REF.chunk_brief(text) == sb.emit_lines(text) and live.CHUNK_CHARS == sb.CHUNK_CHARS


# ── disclosure wording follows the manifest's policy (Stream B request) ─────────────────────────────────────────────

def test_the_disclosure_names_the_manifest_policy_and_claims_all_null_only_under_it():
    assert sb._policy_disclosure("all_null_candidate/1").startswith("all_null_candidate/1 — no numerical result exists")
    other = sb._policy_disclosure("window_qualification/1")
    assert other.startswith("window_qualification/1") and "no numerical result" not in other and "no all-NULL claim" in other
