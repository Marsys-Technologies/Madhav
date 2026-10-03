-- STAND-IN for the data-plane owner's read ACLs (NOT part of Stream B's 1241 — those tables are owned elsewhere): the
-- verifier needs SELECT on the L1 / L0 tables its independent re-derivations read. The runner's identity self-check names
-- the missing L1 read plainly ('verifier lacks SELECT on chart_facts/chart_dashas').
GRANT SELECT ON public.chart_facts, public.chart_dashas, public.bg_transit_rules, public.charts,
                public._migrations_applied TO gochara_verifier;
