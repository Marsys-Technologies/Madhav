-- FIX 9 (P2-B): Deprecate reference_nakshatras
-- reference_nakshatras is superseded by reference_nakshatra (canonical, 28 rows via bg_nakshatra writer)
-- However: l0_reference.py / bg_reference writer still INSERT into this table (see line ~1342).
-- Cannot drop safely without writer refactor. Adding deprecation comment as formal marker.
-- Full drop deferred pending writer migration (bg_reference writer update to stop writing to this table).

COMMENT ON TABLE reference_nakshatras IS 'DEPRECATED — superseded by reference_nakshatra (28 rows, managed by bg_nakshatra writer). Do not add new columns or queries. Kept alive only because bg_reference writer still inserts into it. Remove after bg_reference writer is updated to stop writing here.';
