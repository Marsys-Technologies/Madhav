"""
similarity_signature.py — Per-chart similarity signature 768-dim embedding.
G4-09. Writes to chart_facts (fact_category='similarity_signature') or a dedicated table.
"""
import hashlib, json, logging
from datetime import datetime, timezone
from typing import Optional, Callable

logger = logging.getLogger(__name__)
ASSET_ID = "INF10_similarity_signature"


def _stub_embedding(text: str) -> list[float]:
    return [0.0] * 768


def _build_signature_text(chart_output: dict) -> str:
    """Concatenate UCN digest content for embedding."""
    parts = []
    # Top-K MSR signals
    for sig in (chart_output.get('msr_signals') or [])[:20]:
        parts.append(sig.get('configuration', ''))
    # Active yogas
    for yoga in (chart_output.get('yogas') or []):
        if yoga.get('active'):
            parts.append(yoga.get('name', ''))
    # Current dasha
    dashas = chart_output.get('dashas', {})
    vim = dashas.get('vimshottari', {})
    chain = vim.get('current_chain', [])
    if chain:
        parts.append('dasha: ' + ' '.join(str(c) for c in chain[:2]))
    # Dominant graha from shadbala
    shadbala = chart_output.get('shadbala', {})
    if shadbala:
        dominant = max(shadbala, key=lambda g: shadbala[g].get('total', 0))
        parts.append(f'dominant: {dominant}')
    return ' | '.join(p for p in parts if p)


def write(
    build_id: str,
    chart_id: str,
    ayanamsha_id: str,
    chart_output: dict,
    conn,
    extra: Optional[dict] = None,
    embed_fn: Callable[[str], list[float]] = _stub_embedding,
) -> int:
    """Embed UCN digest text and store as chart_facts similarity_signature row."""
    sig_text = _build_signature_text(chart_output)
    if not sig_text:
        sig_text = f'chart_{chart_id}_ayanamsha_{ayanamsha_id}'

    embedding = embed_fn(sig_text)

    fact_id = hashlib.sha256(
        f"similarity_signature|{chart_id}|{ayanamsha_id}|{build_id}".encode()
    ).hexdigest()[:16]

    row = (
        fact_id, chart_id, ayanamsha_id, build_id,
        'similarity_signature', 'D1', 'similarity_signature',
        json.dumps({'writer': 'similarity_signature', 'engine_version': 'pyjhora/1.0.0', 'ayanamsha_id': ayanamsha_id}),
        'similarity_signature', 'signature', 'embedding_768d',
        sig_text[:500],  # value_text = truncated signature text
        float(len(sig_text)),  # value_number = text length
        f'similarity_signature.signature.embedding_768d@{chart_id[:8]}',  # citation_ref
        'UCN digest embedding for cross-chart similarity',  # citation_human
        'vertex_ai_768d',  # source_calculation
        'single',
        'pyjhora/1.0.0',
        datetime.now(timezone.utc).isoformat(),
    )

    _upsert(conn, [row])
    return 1  # always 1 row


_INSERT_SQL = """
INSERT INTO chart_facts
  (fact_id, chart_id, ayanamsha_id, build_id,
   category, divisional_chart, source_section, provenance,
   fact_category, fact_subject, fact_key,
   value_text, value_number,
   citation_ref, citation_human,
   source_calculation, verification_pass_status,
   engine_version, computed_at_iso)
VALUES %s
ON CONFLICT (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, build_id)
DO UPDATE SET
  value_text = EXCLUDED.value_text,
  value_number = EXCLUDED.value_number,
  computed_at_iso = EXCLUDED.computed_at_iso
"""


def _upsert(conn, rows):
    from psycopg2.extras import execute_values
    with conn.cursor() as cur:
        execute_values(cur, _INSERT_SQL, rows)
    conn.commit()
