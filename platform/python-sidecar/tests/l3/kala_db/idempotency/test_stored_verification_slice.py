"""Replay the six slice DB oracles against the actual migrated TEMP schema."""
import pytest

from tests.l3.kala_db.e2e.conftest import _apply_slice_schema
from tests.l3.kala_db.e2e import test_slice


@pytest.mark.parametrize("oracle", [
    test_slice.test_candidate_read_model_carries_cancelled_state_and_source_ids,
    test_slice.test_registry_query_returns_the_pinned_candidate_and_never_current,
    test_slice.test_testimony_writes_no_numeric_contribution,
    test_slice.test_l4_pratikara_keeps_reading_only_legacy_obstructions,
    test_slice.test_runtime_dict_row_connection_can_run_the_slice,
    test_slice.test_a_published_partition_cannot_be_replaced,
], ids=lambda oracle: oracle.__name__)
def test_stored_verification_slice_schema(conn, oracle):
    _apply_slice_schema(conn)
    oracle(conn)
