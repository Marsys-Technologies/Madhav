-- Migration 195: bg_texts target_floor update — Nadi corpus expansion 13→15 texts
-- Additive ingest of bhrigu_nandi_nadi (608) + nadi_navamsa_patel (1850) = 2,458 new chunks
-- Total: 8,193 (13-text baseline) + 2,458 (Nadi delta) = 10,651
-- Existing 13 texts' chunk counts UNCHANGED (additive model, no DELETE).

UPDATE asset_registry
SET
    target_floor         = 10651,
    volume_explanation   = (
        'Additive Nadi corpus expansion 2026-06-09 (feature/nadi-corpus-expansion): '
        '8,193 (13-text baseline) + 608 (bhrigu_nandi_nadi) + 1,850 (nadi_navamsa_patel) = 10,651. '
        'Floors-are-aspirational policy applied. Full-rebuild mode still available for reproducibility proof. '
        'bhrigu_nandi_nadi: 327pp clean English aphorism prose, Nadi school, MEDIUM provenance. '
        'nadi_navamsa_patel: DjVu OCR ingest, verse-fragment filter applied (>30% non-ASCII lines excluded), '
        'Nadi school, MEDIUM provenance.'
    )
WHERE asset_id = 'bg_texts';
