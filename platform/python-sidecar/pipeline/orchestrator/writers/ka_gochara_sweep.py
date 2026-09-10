"""
pipeline/orchestrator/writers/ka_gochara_sweep.py
Orchestrator registration shim for ka_gochara_sweep (L3 Kāla — D-5 Lane G-4
Forward sweep + serving).

MR-09 DISCOVERABILITY GATE — RETIRED WRITER (2026-08-10)
=========================================================
ka_gochara_sweep is a RETIRED asset.  The W2G / GOCHARA-UTKARSA campaign
introduced the ka_gochara materializer (pipeline/orchestrator/writers/
ka_gochara.py, asset_id='ka_gochara') as the production successor.
The sweep writer must NOT be dispatched for new builds.

SUPERSEDING RULING DISPOSITION (MR-09, cross-ref MR-28):
  - The 2026-06-26 ruling "do NOT add writers/ka_gochara.py to prevent naming
    collision" is superseded.  The naming collision it sought to prevent is
    now resolved by the MR-09 rename: the Python transit service class is
    GocharaTransitService (services/ka_gochara/service.py), while the
    materializer writer is KaGocharaWriter (@register('ka_gochara')).
    These are unambiguously different things with unambiguous names.
  - The formal adjudicated disposition of the 2026-06-26 ruling is recorded
    in MR-28 (ruling reference register).

WHY THE @register IS REMOVED HERE (not just in the DB):
  The orchestrator's _check_writer_registry_gaps() enforces that every
  @register()'d asset_id has has_writer=true in asset_registry.  A retired
  writer that still @registers itself fires this guard on every run start —
  either forcing a perpetual has_writer=true row for an asset that should
  never be dispatched, or producing a writer-gap WARNING on every run.
  Removing the unconditional import here is the correct resolution:
  the implementation in services/ka_gochara_sweep/ is preserved intact
  (reachable for forensic reference or one-off CLI use), but discover_all()
  no longer adds 'ka_gochara_sweep' to the WRITER_REGISTRY.

  If the sweep writer is ever un-retired, restore the import below.

IMPLEMENTATION (services/ka_gochara_sweep/writer.py) IS PRESERVED:
  The KaGocharaSweepWriter class and all sweep/shape_output logic remain
  in services/ka_gochara_sweep/.  Nothing is deleted.  This shim simply
  no longer imports it on discover_all(), which is what prevented the
  @register('ka_gochara_sweep') decorator from firing.

Layer: L3 Kāla · Asset: ka_gochara_sweep · Status: RETIRED
Successor: ka_gochara (pipeline/orchestrator/writers/ka_gochara.py)
"""
# RETIRED — import removed so @register('ka_gochara_sweep') does NOT fire
# during discover_all().  See module docstring for the full reasoning.
#
# To re-enable (only if un-retiring this asset):
#   from services.ka_gochara_sweep.writer import KaGocharaSweepWriter  # noqa: F401

__all__ = []  # nothing registered; shim is a tombstone, not an active entry
