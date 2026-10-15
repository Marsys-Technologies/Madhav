"""N1: reconcile historical comments without rewriting the accepted migration."""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[4]
NOTE = ROOT / "00_ARCHITECTURE/briefs/kalayantra/P06_N1_MIGRATION_COMMENT_RECONCILIATION_v1_0.md"
MIGRATION = ROOT / "platform/migrations/1308_gochara_near_miss_storage.sql"
ACCEPTED_SHA256 = "bc7a220970b91d2d60b1532368e106df673f63a56d573d88acd78857e665204b"


def note():
    assert NOTE.is_file(), "P06-N1 needs its historical-comment reconciliation note"
    return NOTE.read_text(encoding="utf-8")


@pytest.mark.parametrize("correction", [
    "P06 selection: **1305 → 1306 → 1308**. The historical 1307 publication-CHECK slot belongs to P09",
    "FB-26 is **WITHDRAWN**: no `occurrence_kind` column is added to `ka_gochara_relationship_record`",
    "P06b must land before the FB-66 final-rules candidate and before any P08 enablement",
])
def test_n1_reconciles_each_superseded_claim(correction):
    assert correction in note()


def test_n1_binds_accepted_history_and_preserves_sql_bytes_if_present():
    text = note()
    metadata = yaml.safe_load(text.split("---", 2)[1])
    assert metadata["version"] == "1.0"
    assert metadata["status"] == "CURRENT"
    assert metadata["finding"] == "P06-N1"
    assert metadata["accepted_head"] == "adc6b81eab68efe11c64211f51c923c1e84ec24c"
    assert metadata["migration_sha256"] == ACCEPTED_SHA256
    assert "1308_gochara_near_miss_storage.sql:4,51–57" in text
    assert "SURROGATE_ANSWER_18.md:13,32–34" in text
    assert "FINAL_BUILD_SCOPE_v1_0.md:120–123" in text
    assert "W4_P06_FINAL_REVIEW_adc6b81ea.md:41" in text
    assert "Never edit the applied migration" in text
    # P06 is not yet in every pre-build base. Absence is not an applied-migration
    # attestation; once ported, even a comment/whitespace edit must fail this pin.
    if MIGRATION.exists():
        assert hashlib.sha256(MIGRATION.read_bytes()).hexdigest() == ACCEPTED_SHA256


def test_n1_acceptance_is_collected_by_the_governance_shards():
    import ci_shard

    files = ci_shard.test_files()
    shards = ci_shard.partition(files, 5)
    assert Path(__file__).resolve() in files
    assert sum(Path(__file__).resolve() in shard for shard in shards) == 1
    assert ci_shard.verify(files, shards) == []
