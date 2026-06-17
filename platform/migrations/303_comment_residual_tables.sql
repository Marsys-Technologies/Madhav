-- FIX 11 (P3-E): Mark empty residual tables as deprecated
-- classical_chunks: 0 rows — referenced in l0_text_index.py _search_classical_chunks()
--   Cannot drop: live code queries this table. Kept as empty placeholder.
-- prashna_charts: 0 rows — referenced in ga_prashna_writer.py Step 1 check
--   Cannot drop: live code queries this table. Kept as empty placeholder.
-- Both tables are empty because their write paths were superseded but read paths remain.
-- Full cleanup deferred pending refactor of the respective writer/query code.

COMMENT ON TABLE classical_chunks IS 'DEPRECATED — empty placeholder. Superseded by classical_text_chunks (bg_texts). Live code in l0_text_index.py still references this table. Do not drop until that code is updated.';

COMMENT ON TABLE prashna_charts IS 'EMPTY PLACEHOLDER — prashna charts not yet built in production. Table exists as schema skeleton for ga_prashna_writer.py Step 1 lookup. Do not drop until prashna chart build is implemented.';
