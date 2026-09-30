"""Hash honesty and extract-adapter tests (protocol §4.5, §9.1 — condition 4)."""
from __future__ import annotations

import pytest

from services.gochara_eval import InputRejected, load_extract, measure_sha256

from .conftest import (EXTRACT_3_0, EXTRACT_3_0_PIN, needs_campaign,
                       synth_extract, write_json)


class TestHashHonesty:
    def test_hash_is_measured_not_asserted(self, synth_extract_path):
        ext = load_extract(synth_extract_path)
        measured = measure_sha256(synth_extract_path.read_bytes())
        assert ext.sha256["measured"] == measured
        assert ext.sha256["declared_pin"] is None and ext.sha256["match"] is True

    def test_tampered_extract_rejected(self, tmp_path, synth_extract_path):
        # flip one byte in a copy of a pinned extract (protocol condition 4)
        raw = bytearray(synth_extract_path.read_bytes())
        raw[-3] ^= 0xFF
        tampered = tmp_path / "tampered.json"
        tampered.write_bytes(bytes(raw))
        pin = measure_sha256(synth_extract_path.read_bytes())
        with pytest.raises(InputRejected, match="sha256"):
            load_extract(tampered, declared_pin=pin)

    def test_matching_pin_passes(self, synth_extract_path):
        pin = measure_sha256(synth_extract_path.read_bytes())
        ext = load_extract(synth_extract_path, declared_pin=pin)
        assert ext.sha256 == {"declared_pin": pin, "measured": pin,
                              "match": True}


class TestInputAdapter:
    def test_negative_si_rejected(self, tmp_path):
        rows = [{"event_class": "marriage", "ws": "2013-11-01",
                 "we": "2014-01-01", "pk": "2013-12-11", "si": -0.2,
                 "valence": "gain"}]
        path = write_json(tmp_path / "x.json", synth_extract(rows))
        with pytest.raises(InputRejected, match="si < 0"):
            load_extract(path)

    def test_unknown_class_rejected(self, tmp_path):
        rows = [{"event_class": "alien_contact", "ws": "2010-01-01",
                 "we": "2010-02-01", "pk": "2010-01-15", "si": 0.1,
                 "valence": "neutral"}]
        path = write_json(tmp_path / "x.json", synth_extract(rows))
        with pytest.raises(InputRejected, match="27-class"):
            load_extract(path)

    def test_merge_representative_max_si_ties_earliest_peak(self, tmp_path):
        # two abutting windows (we 2010-01-31, next ws 2010-02-01) merge into
        # one candidate; equal si -> earliest peak wins (§4.2)
        rows = [
            {"event_class": "marriage", "ws": "2010-01-01", "we": "2010-01-31",
             "pk": "2010-01-10", "si": 0.5, "valence": "gain"},
            {"event_class": "marriage", "ws": "2010-02-01", "we": "2010-02-28",
             "pk": "2010-02-05", "si": 0.5, "valence": "gain"},
        ]
        path = write_json(tmp_path / "x.json", synth_extract(rows))
        ext = load_extract(path)
        [w] = ext.merged["marriage"]
        assert (w.ws.isoformat(), w.we.isoformat()) == ("2010-01-01", "2010-02-28")
        assert w.pk.isoformat() == "2010-01-10" and w.si == 0.5
        assert ext.dedup_table["marriage"] == [2, 1]

    def test_merge_higher_si_wins(self, tmp_path):
        rows = [
            {"event_class": "surgery", "ws": "2010-01-01", "we": "2010-01-31",
             "pk": "2010-01-10", "si": 0.5, "valence": "loss"},
            {"event_class": "surgery", "ws": "2010-01-15", "we": "2010-02-10",
             "pk": "2010-02-01", "si": 0.9, "valence": "loss"},
        ]
        path = write_json(tmp_path / "x.json", synth_extract(rows))
        ext = load_extract(path)
        [w] = ext.merged["surgery"]
        assert w.pk.isoformat() == "2010-02-01" and w.si == 0.9


@needs_campaign
class TestRealExtract:
    def test_pinned_3_0_extract_measures_to_declared_pin(self):
        ext = load_extract(EXTRACT_3_0, declared_pin=EXTRACT_3_0_PIN)
        assert ext.sha256["match"] is True
        assert ext.row_count == 914
        # v2.3 §4.5 corrected claim: all four valences present
        assert set(ext.valence_domain) == {"gain", "loss", "mixed", "neutral"}
        assert ext.valence_domain["mixed"] == 134
        assert ext.valence_domain["neutral"] == 180
