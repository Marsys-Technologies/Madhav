"""
ga_writers — L1 Gaṇita build writers for chart_facts, ganita_positions,
ganita_dashas, chart_divisionals.

GA3: ga_positions_writer.py  → ganita_positions
     ga_strength_writer.py   → chart_facts (shadbala + ashtakavarga + bhava_bala)
GA4: ga_panchanga_writer.py  → chart_facts  [separate brief]
GA5: ga_sensitive_writer.py  → chart_facts  [separate brief]
GA6: ga_vargas_writer.py     → chart_divisionals [separate brief]
GA7: ga_dashas_writer.py     → ganita_dashas [separate brief]

Every writer:
  - Uses PyJHora (pyjhora_adapter) as the sole computation engine.
  - Performs FORENSIC gate before any INSERT.
  - Uses atomic-grain (one queryable sub-value = one row).
  - Writes dual citations (citation_ref + citation_human).
  - Uses sha256-based fact_id for chart_facts rows.
  - No audience tier, no LLM content in data rows.
"""
