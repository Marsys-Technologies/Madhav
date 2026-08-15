"""
brahmagyan.phala.confidence_vocab — canonical confidence_basis vocabulary.

Two-value vocabulary for phala_anchors.confidence_basis.
Named constants so no writer ever spells the string twice (§N.4, CLAUDE.md).

  STRUCTURAL_NOT_YET_EMPIRICAL  — L4 structural derivation; no empirical calibration.
  CALIBRATED_EMPIRICAL          — L5 Mīmāṃsā calibrated; only ph_sodhana may emit.

ph_sodhana detects any value != STRUCTURAL_NOT_YET_EMPIRICAL as layer_leakage
(services/ph_sodhana/engine.py:detect_layer_leakage). Writers that are not ph_sodhana
MUST use STRUCTURAL_NOT_YET_EMPIRICAL.

WHY IT LIVES IN L0 (brahmagyan) rather than beside the phala writers:
confidence_basis is a cross-layer contract between ph_nimitta (L4 writer),
ph_sankrama (L4 writer), and ph_sodhana (L4 anomaly detector). Putting it
under any one service would require the others to import a sibling. L0 brahmagyan
is the foundation layer every other layer may depend on without circular deps —
the same rationale that placed brahmagyan.verification_vocab here.

Finding F-68 (EKAVĀKYATĀ B-07): before this module, all three sites spelled
'structural_not_yet_empirical' as a bare string literal, violating §N.4.
"""
from __future__ import annotations

from typing import Final

#: Default for all L4 phala anchor writers. Means: "this anchor was derived from
#: structural astrology (dashas, yogas, transits) with no empirical posterior applied."
#: L5 Mīmāṃsā (ph_sodhana) enforces via LEAKAGE-FIREWALL: any anchor that escapes L4
#: with a different basis value is flagged as l5_calibration_attempted contamination.
STRUCTURAL_NOT_YET_EMPIRICAL: Final[str] = 'structural_not_yet_empirical'

#: Reserved for L5 Mīmāṃsā only. Only ph_sodhana may ever write this value;
#: ph_nimitta and ph_sankrama must never emit it. The LEAKAGE-FIREWALL (detect_layer_leakage)
#: exists precisely to catch any L4 writer that mistakenly emits this.
CALIBRATED_EMPIRICAL: Final[str] = 'calibrated_empirical'
