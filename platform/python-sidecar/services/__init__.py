"""
services/ — L3+ layer service modules for the MARSYS-JIS sidecar.

Each sub-package is a ka_* (L3 Kāla) or ph_* (L4 Phala) service asset.
Service assets produce no domain rows; they register with the orchestrator
via a WriterBase subclass that runs a FORENSIC self-test and writes
service_health to asset_registry.

Current assets:
  ka_muhurta_seva  — Panchāṅga-Muhūrta service (L3 Kāla K1)
"""
