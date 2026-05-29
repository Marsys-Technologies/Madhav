"""
test_g29_timing_rules.py — Tests for G29 Classical Timing Rule Catalog.

Covers:
  1. len(G29_RULES) >= 200
  2. All required keys present per rule
  3. source_text only from allowed set
  4. strength_qualifier only from allowed set
  5. rule_id unique across all rules
  6. seed_g29_rules() idempotent (run twice, count unchanged)
  7. DB row count >= 200 after seed (integration test, staging-only)
  8. bphs rules >= 65; jaimini >= 30; tajik >= 30; kp >= 20; saravali >= 20; nadi >= 25

G29 [BUILD-ORCH-STREAM-C-G29-S1]
"""

import os
import pytest

from pipeline.classical_timing_rules import G29_RULES, seed_g29_rules

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REQUIRED_KEYS = {
    "rule_id",
    "source_text",
    "rule_category",
    "timing_system",
    "trigger_predicate",
    "predicted_outcome",
    "activation_window",
    "strength_qualifier",
    "classical_citation",
}

ALLOWED_SOURCE_TEXTS = {
    "bphs", "phaladeepika", "jaimini_sutram", "tajik", "kp", "saravali", "nadi"
}

ALLOWED_STRENGTH_QUALIFIERS = {"strong", "moderate", "weak", "conditional"}

# ---------------------------------------------------------------------------
# DB connection helper
# ---------------------------------------------------------------------------

DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = os.environ.get("DB_PORT", "5433")
DB_USER = os.environ.get("DB_USER", "amjis_app")
DB_PASS = os.environ.get("DB_PASS", "aYtv6SN5TwRBShzHfxN4Qz_ccW3a49qnCAA2L-VF")
DB_NAME = os.environ.get("DB_NAME", "amjis_staging")


def _get_conn():
    """Return a psycopg2 connection to staging DB, or raise if unavailable."""
    import psycopg2
    return psycopg2.connect(
        host=DB_HOST, port=int(DB_PORT), user=DB_USER,
        password=DB_PASS, dbname=DB_NAME,
        connect_timeout=3,
    )


def _db_reachable() -> bool:
    try:
        conn = _get_conn()
        conn.close()
        return True
    except Exception:
        return False


DB_AVAILABLE = _db_reachable()

# ---------------------------------------------------------------------------
# Test 1 — Corpus size
# ---------------------------------------------------------------------------

def test_g29_rules_minimum_count():
    """G29_RULES must contain at least 200 timing rules."""
    assert len(G29_RULES) >= 200, (
        f"Expected >= 200 rules, got {len(G29_RULES)}"
    )


# ---------------------------------------------------------------------------
# Test 2 — Required keys present on every rule
# ---------------------------------------------------------------------------

def test_all_required_keys_present():
    """Every rule dict must contain all required column keys."""
    for rule in G29_RULES:
        missing = REQUIRED_KEYS - set(rule.keys())
        assert not missing, (
            f"Rule '{rule.get('rule_id', '?')}' missing keys: {missing}"
        )


# ---------------------------------------------------------------------------
# Test 3 — source_text from allowed set
# ---------------------------------------------------------------------------

def test_source_text_values():
    """source_text must be one of the 7 allowed classical texts."""
    for rule in G29_RULES:
        assert rule["source_text"] in ALLOWED_SOURCE_TEXTS, (
            f"Rule '{rule['rule_id']}' has invalid source_text: '{rule['source_text']}'"
        )


# ---------------------------------------------------------------------------
# Test 4 — strength_qualifier from allowed set
# ---------------------------------------------------------------------------

def test_strength_qualifier_values():
    """strength_qualifier must be one of: strong, moderate, weak, conditional."""
    for rule in G29_RULES:
        assert rule["strength_qualifier"] in ALLOWED_STRENGTH_QUALIFIERS, (
            f"Rule '{rule['rule_id']}' has invalid strength_qualifier: "
            f"'{rule['strength_qualifier']}'"
        )


# ---------------------------------------------------------------------------
# Test 5 — rule_id unique
# ---------------------------------------------------------------------------

def test_rule_ids_unique():
    """All rule_id values must be unique across the corpus."""
    ids = [rule["rule_id"] for rule in G29_RULES]
    duplicates = [rid for rid in set(ids) if ids.count(rid) > 1]
    assert not duplicates, f"Duplicate rule_ids found: {duplicates}"


# ---------------------------------------------------------------------------
# Test 6 — seed_g29_rules() idempotent (integration, skipped if DB unreachable)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not DB_AVAILABLE, reason="Staging DB not reachable at 127.0.0.1:5433")
def test_seed_idempotent():
    """seed_g29_rules() is idempotent: running twice leaves row count unchanged."""
    conn = _get_conn()
    try:
        # First seed
        seed_g29_rules(conn)

        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM g29_timing_rules")
            count_after_first = cur.fetchone()[0]

        # Second seed — should insert 0 additional rows
        inserted_second = seed_g29_rules(conn)

        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM g29_timing_rules")
            count_after_second = cur.fetchone()[0]

        assert inserted_second == 0, (
            f"Second seed inserted {inserted_second} rows; expected 0 (idempotent)"
        )
        assert count_after_first == count_after_second, (
            f"Row count changed after second seed: {count_after_first} → {count_after_second}"
        )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Test 7 — DB row count >= 200 after seed (integration)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not DB_AVAILABLE, reason="Staging DB not reachable at 127.0.0.1:5433")
def test_db_row_count_after_seed():
    """After seeding, g29_timing_rules must contain at least 200 rows."""
    conn = _get_conn()
    try:
        seed_g29_rules(conn)
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM g29_timing_rules")
            count = cur.fetchone()[0]
        assert count >= 200, (
            f"Expected >= 200 rows in g29_timing_rules after seed, got {count}"
        )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Test 8 — Per-source distribution meets minimums
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not DB_AVAILABLE, reason="Staging DB not reachable at 127.0.0.1:5433")
def test_per_source_distribution():
    """
    Per-source row counts after seeding must meet spec minimums:
      bphs >= 65, jaimini_sutram >= 30, tajik >= 30,
      kp >= 20, saravali >= 20, nadi >= 25
    """
    conn = _get_conn()
    try:
        seed_g29_rules(conn)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT source_text, COUNT(*) FROM g29_timing_rules GROUP BY source_text"
            )
            dist = dict(cur.fetchall())
    finally:
        conn.close()

    minimums = {
        "bphs": 65,
        "jaimini_sutram": 30,
        "tajik": 30,
        "kp": 20,
        "saravali": 20,
        "nadi": 25,
    }
    for source, minimum in minimums.items():
        actual = dist.get(source, 0)
        assert actual >= minimum, (
            f"source_text='{source}' has {actual} rows; expected >= {minimum}"
        )


# ---------------------------------------------------------------------------
# Additional in-memory distribution check (no DB needed)
# ---------------------------------------------------------------------------

def test_per_source_distribution_in_memory():
    """
    In-memory source distribution must meet spec minimums:
      bphs >= 65, phaladeepika >= 30, jaimini_sutram >= 30, tajik >= 30,
      kp >= 20, saravali >= 20, nadi >= 25
    """
    from collections import Counter
    dist = Counter(rule["source_text"] for rule in G29_RULES)

    minimums = {
        "bphs": 65,
        "phaladeepika": 30,
        "jaimini_sutram": 30,
        "tajik": 30,
        "kp": 20,
        "saravali": 20,
        "nadi": 25,
    }
    for source, minimum in minimums.items():
        actual = dist[source]
        assert actual >= minimum, (
            f"In-memory: source_text='{source}' has {actual} rules; expected >= {minimum}"
        )
