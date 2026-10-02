-- PENDING (Stream B owns the migration): the verifier principal's read set + the 1206 inventory-verification write the
-- separate verification job needs, which no reviewed migration gives it yet (1240 §7 grants the verifier the 1240 table
-- and its own read set; 1206 §7 grants the BUILDER the inventory-verification table — PC-4 removes that). Derived by running
-- the job as the verifier on the faithful mirror and adding one grant per `permission denied` until it converged; the
-- `individually_necessary` test proves each line is needed.
GRANT SELECT, INSERT, DELETE ON public.ka_gochara_search_inventory_verification TO gochara_verifier;
GRANT SELECT ON public.ka_gochara_search_obligation TO gochara_verifier;
-- the job ends in the SAME candidate gate the seal uses (a read-only function)
GRANT EXECUTE ON FUNCTION public.ka_gochara_window_verification_violations(uuid, text) TO gochara_verifier;
GRANT SELECT ON public.ka_gochara_rule_path_prerequisite TO gochara_verifier;
GRANT SELECT ON public.ka_gochara_predicate TO gochara_verifier;
GRANT SELECT ON public.ka_gochara_sky_convention TO gochara_verifier;
