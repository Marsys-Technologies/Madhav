-- STAND-IN for Stream B's 1241 (R10-4 iii): the verifier job now ENDS in the combined candidate gate
-- (ka_gochara_candidate_gate_violations = 1206/1232 completeness + 1240 window verification), as the sealer's trigger does.
-- 1240 grants the verifier EXECUTE on the combined function itself; what the 1206/1232 completeness function reads as the
-- INVOKER is the sealer's list in 1241, of which the verifier holds none. This delta was derived the 1206-R6 way — run the
-- job's final gate as the verifier on the composed fixture and add one grant per `permission denied` until it converged
-- (tests/l3/gochara/test_a53_r10_complete_records.py::test_the_verifier_combined_gate_delta_is_exactly_this).
-- It belongs in 1241 (Stream B's file); it is applied here only so the faithful mirror's verifier can run the gate.
GRANT EXECUTE ON FUNCTION public.ka_gochara_search_completeness_violations(uuid, text) TO gochara_verifier;
GRANT EXECUTE ON FUNCTION public.ka_gochara_search_l1_facts_digest(uuid, text[]) TO gochara_verifier;
GRANT EXECUTE ON FUNCTION public.ka_gochara_search_dasha_digest(uuid, uuid[]) TO gochara_verifier;
GRANT SELECT ON public.ka_gochara_convention_bridge TO gochara_verifier;
GRANT EXECUTE ON FUNCTION public.ka_gochara_search_inventory_digest(uuid, text, text) TO gochara_verifier;
GRANT EXECUTE ON FUNCTION public.ka_gochara_search_ledger_digest(uuid, text, text) TO gochara_verifier;
GRANT EXECUTE ON FUNCTION public.ka_gochara_search_inventory_preimage(uuid, text, text) TO gochara_verifier;
GRANT EXECUTE ON FUNCTION public.ka_gochara_utc_ts(timestamp with time zone) TO gochara_verifier;
GRANT EXECUTE ON FUNCTION public.ka_gochara_search_moon_scope_violations(uuid, text) TO gochara_verifier;
GRANT EXECUTE ON FUNCTION public.ka_gochara_search_moon_resolved_domain(uuid, text, text, uuid) TO gochara_verifier;

-- STAND-IN for Stream B's 1241 (R11-3): the SEALER writes the approval receipt and calls the missing-receipt check in the sealing
-- transaction (1240 creates the table and the function and grants nothing on them; the grants are 1241's).
DO $$ BEGIN
  IF to_regrole('gochara_sealer') IS NOT NULL THEN
    GRANT SELECT, INSERT ON public.ka_gochara_seal_approval TO gochara_sealer;
    GRANT EXECUTE ON FUNCTION public.ka_gochara_seal_receipt_missing(uuid, text) TO gochara_sealer;
  END IF;
END $$;

-- STAND-IN for Stream B's 1241 (R12-1): the brief and the generation-wide job check read the LEGACY projection relations for the
-- generation (none may exist) and the publication digest reads kala_gochara_contacts; the sealer already holds both in 1241.
GRANT SELECT ON public.kala_gochara_contacts TO gochara_verifier;
DO $$ BEGIN
  IF to_regclass('public.kala_gochara_windows') IS NOT NULL THEN
    GRANT SELECT (chart_id, generation) ON public.kala_gochara_windows TO gochara_verifier;
  END IF;
END $$;

-- STAND-IN for Stream B's 1241 (R12-1): EXECUTE on the new legacy-rows gate helper for both principals (1240 creates it and grants nothing;
-- 1241's closed ACL spec refuses a grant it does not list).
GRANT EXECUTE ON FUNCTION public.ka_gochara_legacy_projection_rows(uuid, text) TO gochara_verifier;
DO $$ BEGIN
  IF to_regrole('gochara_sealer') IS NOT NULL THEN
    GRANT EXECUTE ON FUNCTION public.ka_gochara_legacy_projection_rows(uuid, text) TO gochara_sealer;
  END IF;
END $$;

-- (F-R12-4's seal-brief grants are now Stream B's 1241 v6, PR #2949 — the stand-in that was here is removed so the real migration is what the suites prove.)
