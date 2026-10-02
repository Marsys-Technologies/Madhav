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
